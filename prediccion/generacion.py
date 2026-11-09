"""Generación de predicciones en segundo plano (hilo + estado en disco).

El entrenamiento (ARIMA/SARIMA/XGBoost) tarda varios minutos, así que no
se ejecuta dentro de un callback de Dash: se lanza en un hilo daemon y su
estado se persiste en archivos dentro de la carpeta de resultados de la sesión.
Cualquier worker de gunicorn puede leer ese estado, de modo que el polling del
navegador funciona aunque el hilo corra en otro worker.

El hilo emite un latido cada SEGUNDOS_LATIDO y reporta su avance. Si el
servidor muere o se reinicia, los latidos cesan y leer_estado pasa a
"interrumpido" como máximo SEGUNDOS_SIN_SENAL después, en lugar de dejar el
estado en "running" para siempre. El tiempo mostrado al usuario es el tiempo
real transcurrido desde el inicio.
"""
import json
import os
import threading
import time
import uuid

from sesion import dir_resultados

ARCHIVO_ESTADO = "estado_generacion.json"
ARCHIVO_LOCK = "generacion.lock"

SEGUNDOS_LATIDO = 10
SEGUNDOS_SIN_SENAL = 120

CLASES_ALERTA = {
    "idle": "alert alert-secondary",
    "running": "alert alert-info",
    "done": "alert alert-success",
    "error": "alert alert-danger",
    "interrumpido": "alert alert-warning",
}

# Serializa las escrituras del hilo de generación y de su hilo de latido
# (ambos viven en el mismo proceso). Entre procesos, os.replace es atómico.
_mutex_estado = threading.Lock()


def _ruta(session_id, nombre):
    return os.path.join(dir_resultados(session_id), nombre)


def _estado_en_crudo(session_id):
    """Lee el estado tal cual está en disco (sin aplicar reglas de staleness)."""
    try:
        with open(_ruta(session_id, ARCHIVO_ESTADO), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"estado": "idle", "mensaje": "", "ts": 0.0, "latido": 0.0}


def leer_estado(session_id):
    """Estado de la generación en curso o de la última.

    Estados: idle, running, done, error e interrumpido (running cuyo último
    latido ya superó SEGUNDOS_SIN_SENAL, típicamente por un reinicio).
    """
    estado = _estado_en_crudo(session_id)
    latido = estado.get("latido") or estado.get("ts", 0.0)

    if (
        estado.get("estado") == "running"
        and time.time() - latido > SEGUNDOS_SIN_SENAL
    ):
        return {
            "estado": "interrumpido",
            "mensaje": (
                "La generación se interrumpió (el servidor dejó de emitir "
                "señales). Inténtalo de nuevo."
            ),
            "ts": estado.get("ts", 0.0),
            "latido": latido,
        }
    return estado


def presentacion(estado):
    """(texto, clase CSS) listos para mostrar el estado en la pestaña."""
    texto = estado.get("mensaje", "")
    if estado.get("estado") == "running":
        segundos = max(0, int(time.time() - estado.get("ts", time.time())))
        texto = (
            f"⏳ {texto} (transcurrido: {segundos // 60} min "
            f"{segundos % 60} s)"
        )
    clase = CLASES_ALERTA.get(estado.get("estado", "idle"), "alert alert-info")
    return texto, clase


def _guardar_estado(session_id, datos):
    ruta = _ruta(session_id, ARCHIVO_ESTADO)
    archivo_temporal = ruta + ".tmp"
    with open(archivo_temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    os.replace(archivo_temporal, ruta)


def _nuevo_estado(session_id, estado_nuevo, mensaje):
    with _mutex_estado:
        previo = _estado_en_crudo(session_id)
        ahora = time.time()
        inicio = (
            previo.get("ts", ahora)
            if previo.get("estado") == "running"
            else ahora
        )
        _guardar_estado(
            session_id,
            {"estado": estado_nuevo, "mensaje": mensaje,
             "ts": inicio, "latido": ahora},
        )


def _registrar_avance(session_id, mensaje=None):
    """Actualiza el latido y, si se indica, el mensaje. Solo si sigue running."""
    with _mutex_estado:
        estado = _estado_en_crudo(session_id)
        if estado.get("estado") != "running":
            return
        estado["latido"] = time.time()
        if mensaje is not None:
            estado["mensaje"] = mensaje
        _guardar_estado(session_id, estado)


def _tomar_lock(ruta_lock):
    """Crea el lock de forma atómica; devuelve su token o None si ya existe."""
    token = uuid.uuid4().hex
    try:
        fd = os.open(ruta_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, token.encode("ascii"))
        os.close(fd)
        return token
    except FileExistsError:
        return None


def _liberar_lock(ruta_lock, token):
    """Elimina el lock solo si sigue siendo el nuestro (evita borrar otro)."""
    try:
        with open(ruta_lock, encoding="ascii") as f:
            contenido = f.read().strip()
    except OSError:
        return
    # En Windows no se puede borrar un archivo abierto: cerrar antes de remove.
    if contenido == token:
        try:
            os.remove(ruta_lock)
        except OSError:
            pass


def iniciar_generacion(session_id):
    """Lanza la generación en un hilo daemon. Devuelve (iniciado, mensaje)."""
    if leer_estado(session_id)["estado"] == "running":
        return False, "Ya hay una generación en curso; espera a que termine."

    ruta_lock = _ruta(session_id, ARCHIVO_LOCK)
    # El estado ya no dice "running": cualquier lock existente es huérfano.
    try:
        os.remove(ruta_lock)
    except OSError:
        pass

    token = _tomar_lock(ruta_lock)
    if token is None:
        return False, "Ya hay una generación en curso; espera a que termine."

    _nuevo_estado(
        session_id,
        "running",
        "Generando predicciones con ARIMA, SARIMA y XGBoost…",
    )
    threading.Thread(
        target=_ejecutar, args=(session_id, ruta_lock, token), daemon=True
    ).start()
    return True, "Generación iniciada."


def _latir(session_id, detener):
    """Hilo que mantiene fresco el latido mientras la generación está en curso."""
    while not detener.wait(SEGUNDOS_LATIDO):
        _registrar_avance(session_id)


def _ejecutar(session_id, ruta_lock, token):
    """Corre en el hilo: entrena los modelos y escribe el estado final."""
    detener = threading.Event()
    hilo_latido = threading.Thread(
        target=_latir, args=(session_id, detener), daemon=True
    )
    hilo_latido.start()
    try:
        # Import perezoso: tensorflow/xgboost solo se cargan al generar.
        from prediccion.prediction import generar_resultados

        resultado = generar_resultados(
            session_id,
            al_avanzar=lambda texto: _registrar_avance(
                session_id, f"Generando predicciones — {texto}"
            ),
        )
        ganadores = resultado.get("ganadores") if resultado else None
        if ganadores is None or ganadores.empty:
            _nuevo_estado(
                session_id,
                "done",
                "⚠️ Datos insuficientes: se requieren al menos 15 trimestres "
                "(≈4 años) de datos válidos para generar predicciones.",
            )
        else:
            _nuevo_estado(
                session_id, "done", "✅ Predicciones generadas correctamente."
            )
    except FileNotFoundError:
        _nuevo_estado(
            session_id,
            "done",
            "⚠️ Aún no hay datos cargados: sube al menos 4 años (15 "
            "trimestres) para generar predicciones.",
        )
    except Exception as e:
        _nuevo_estado(
            session_id, "error", f"❌ Error al generar predicciones: {e}"
        )
    finally:
        detener.set()
        _liberar_lock(ruta_lock, token)
