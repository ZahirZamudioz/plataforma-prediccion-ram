"""Orquestación de la evaluación de modelos y generación de predicciones futuras."""
import pandas as pd

from prediccion.preprocessing import cargar_datos, obtener_combinaciones_validas
from prediccion.resultados import guardar_resultados
from prediccion.models.arima import entrenar_arima, predecir_arima
from prediccion.models.sarima import entrenar_sarima, predecir_sarima

from prediccion.models.xgboost import entrenar_xgboost, predecir_xgboost


MODELOS = {
    "SARIMA": {"entrenar": entrenar_sarima, "predecir": predecir_sarima},
    "ARIMA": {"entrenar": entrenar_arima, "predecir": predecir_arima},
    
    "XGBoost": {"entrenar": entrenar_xgboost, "predecir": predecir_xgboost},
}


def _avisar(al_avanzar, texto):
    """Notifica el avance sin que un fallo de la notificación corte el pipeline."""
    if al_avanzar is None:
        return
    try:
        al_avanzar(texto)
    except Exception:
        pass


def evaluar_modelos(
    df_long,
    combinaciones_validas,
    df_trimestres_finales,
    al_avanzar=None
):
    """
    Entrena los tres modelos para cada combinación válida y
    devuelve un DataFrame con las métricas de cada uno.
    """
    filas = []
    total = len(combinaciones_validas) * len(MODELOS)
    hecho = 0

    for _, fila in combinaciones_validas.iterrows():
        especie = fila["especie"]
        antibiotico = fila["antibiotico"]

        for nombre, modelos in MODELOS.items():
            hecho += 1
            _avisar(
                al_avanzar,
                f"evaluando modelos ({hecho}/{total}): {especie} · "
                f"{antibiotico} · {nombre}",
            )
            try:
                resultado = modelos["entrenar"](
                    df_long,
                    df_trimestres_finales,
                    especie,
                    antibiotico,
                )
                if resultado is not None:
                    filas.append(resultado["metricas"])
            except Exception:
                continue

    return pd.DataFrame(filas)


def seleccionar_ganador(df_metricas, metrica="rmse"):
    """
    Elige el mejor modelo por combinación según la métrica
    (por defecto RMSE, menor es mejor, igual que el proyecto original).
    """
    if df_metricas.empty:
        return pd.DataFrame(columns=["especie", "antibiotico", "modelo"])

    return (
        df_metricas
        .sort_values(
            ["especie", "antibiotico", metrica],
            na_position="last",
        )
        .groupby(["especie", "antibiotico"], as_index=False)
        .first()
    )


def generar_predicciones_futuras(
    df_long,
    combinaciones_validas,
    df_trimestres_finales,
    ganadores,
    al_avanzar=None
):
    """
    Re-entrena el modelo ganador de cada combinación con toda la serie
    y genera las predicciones de los próximos 4 trimestres.
    """
    filas = []
    total = len(ganadores)

    for indice, (_, fila) in enumerate(ganadores.iterrows(), start=1):
        especie = fila["especie"]
        antibiotico = fila["antibiotico"]
        modelo = fila["modelo"]

        _avisar(
            al_avanzar,
            f"generando predicciones futuras ({indice}/{total}): {especie} · "
            f"{antibiotico} · {modelo}",
        )
        try:
            resultado = MODELOS[modelo]["predecir"](
                df_long,
                df_trimestres_finales,
                especie,
                antibiotico,
            )
            if resultado is not None:
                resultado["especie"] = especie
                resultado["antibiotico"] = antibiotico
                resultado["modelo"] = modelo
                filas.append(resultado)
        except Exception:
            continue

    if not filas:
        return pd.DataFrame(
            columns=["trimestre", "especie", "antibiotico", "modelo", "valor", "tipo"]
        )

    return pd.concat(filas, ignore_index=True)[
        ["trimestre", "especie", "antibiotico", "modelo", "valor", "tipo"]
    ]


def generar_resultados(
    session_id,
    minimo_trimestres=15,
    metrica="rmse",
    al_avanzar=None
):
    """
    Pipeline completo: carga datos de la sesión, evalúa modelos, elige ganador
    por combinación (RMSE, como el proyecto original), genera predicciones
    futuras y guarda los pickles en <sesión>/resultados/ (predicciones.pkl y
    ganadores.pkl).

    ``al_avanzar`` es un callback opcional (str) -> None para reportar avance.
    """
    df_long = cargar_datos(session_id)

    combinaciones_validas, df_trimestres_finales = obtener_combinaciones_validas(
        df_long,
        minimo_trimestres=minimo_trimestres,
    )

    df_metricas = evaluar_modelos(
        df_long,
        combinaciones_validas,
        df_trimestres_finales,
        al_avanzar=al_avanzar,
    )

    ganadores = seleccionar_ganador(df_metricas, metrica=metrica)

    predicciones = generar_predicciones_futuras(
        df_long,
        combinaciones_validas,
        df_trimestres_finales,
        ganadores,
        al_avanzar=al_avanzar,
    )

    guardar_resultados(predicciones, ganadores, session_id)

    return {
        "predicciones": predicciones,
        "ganadores": ganadores,
        "metricas": df_metricas,
    }
