"""Genera bases de datos sintéticas (2021-2025) listas para subir a la app.

Cada archivo ``data/sinteticos/datos_YYYY.xlsx`` contiene una fila por aislado
con las columnas que espera la plataforma:

    fecha, SPEC_NUM, Tipo de localizacion, Tipo de muestra, Edad, especie
    + una columna por antibiótico (nombre final en español)

Los valores de los antibióticos son MIC en texto (``<=0,25``, ``16``, ``>=128``)
elegidos de forma coherente con los puntos de corte CLSI 2025 y con las
combinaciones especie-antibiótico que realmente tienen punto de corte.

Los datos son ficticios: no tienen validez clínica ni epidemiológica.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

RUTA_DICCIONARIOS = os.path.join(BASE_DIR, "data", "Lista_antimicrobianos.xlsx")
RUTA_MAPEO = os.path.join(BASE_DIR, "data", "Lista_especie_especifico_general.xlsx")
RUTA_CLSI = os.path.join(BASE_DIR, "data", "Lista_CLSI_completa.xlsx")
SALIDA_POR_DEFECTO = os.path.join(BASE_DIR, "data", "sinteticos")

# Especies incluidas (códigos de la columna especie_3 del diccionario).
ESPECIES = {
    "eco": {"peso": 0.27, "edad_media": 55},
    "kpn": {"peso": 0.20, "edad_media": 60},
    "pae": {"peso": 0.18, "edad_media": 65},
    "aba": {"peso": 0.15, "edad_media": 65},
    "sau": {"peso": 0.20, "edad_media": 45},
}

# Antibióticos por especie. Solo combinaciones con punto de corte CLSI 2025.
PANELES = {
    "eco": ["Amicacina", "Ceftazidima", "Ceftriaxona", "Ciprofloxacino", "Meropenem"],
    "kpn": ["Amicacina", "Ceftazidima", "Ceftriaxona", "Ciprofloxacino", "Meropenem"],
    "pae": ["Amicacina", "Aztreonam", "Ceftazidima", "Ciprofloxacino", "Meropenem"],
    "aba": ["Amicacina", "Ceftazidima", "Ceftriaxona", "Ciprofloxacino", "Meropenem"],
    "sau": ["Clindamicina", "Ciprofloxacino", "Gentamicina", "Oxacilina", "Vancomicina"],
}

# Orden de columnas de antibióticos en los Excel.
ANTIBIOTICOS = [
    "Amicacina",
    "Aztreonam",
    "Ceftazidima",
    "Ceftriaxona",
    "Ciprofloxacino",
    "Clindamicina",
    "Gentamicina",
    "Meropenem",
    "Oxacilina",
    "Vancomicina",
]

# Perfil por combinación: (probabilidad base de R en 2021, probabilidad de I,
# tendencia anual absoluta, amplitud estacional).
PERFILES = {
    ("eco", "Amicacina"): (0.03, 0.03, 0.05, 0.02),
    ("eco", "Ceftazidima"): (0.10, 0.04, 0.08, 0.03),
    ("eco", "Ceftriaxona"): (0.18, 0.04, 0.09, 0.04),
    ("eco", "Ciprofloxacino"): (0.25, 0.04, 0.07, 0.05),
    ("eco", "Meropenem"): (0.01, 0.02, 0.03, 0.01),
    ("kpn", "Amicacina"): (0.05, 0.03, 0.06, 0.02),
    ("kpn", "Ceftazidima"): (0.18, 0.05, 0.10, 0.04),
    ("kpn", "Ceftriaxona"): (0.25, 0.05, 0.10, 0.05),
    ("kpn", "Ciprofloxacino"): (0.30, 0.04, 0.08, 0.05),
    ("kpn", "Meropenem"): (0.03, 0.02, 0.06, 0.02),
    ("pae", "Amicacina"): (0.10, 0.04, 0.05, 0.03),
    ("pae", "Aztreonam"): (0.15, 0.04, 0.06, 0.04),
    ("pae", "Ceftazidima"): (0.12, 0.05, 0.07, 0.04),
    ("pae", "Ciprofloxacino"): (0.18, 0.04, 0.06, 0.05),
    ("pae", "Meropenem"): (0.10, 0.04, 0.08, 0.04),
    ("aba", "Amicacina"): (0.35, 0.05, 0.05, 0.04),
    ("aba", "Ceftazidima"): (0.45, 0.06, 0.06, 0.05),
    ("aba", "Ceftriaxona"): (0.50, 0.05, 0.05, 0.05),
    ("aba", "Ciprofloxacino"): (0.45, 0.05, 0.05, 0.05),
    ("aba", "Meropenem"): (0.40, 0.05, 0.08, 0.05),
    ("sau", "Clindamicina"): (0.12, 0.03, 0.05, 0.03),
    ("sau", "Ciprofloxacino"): (0.20, 0.03, 0.05, 0.04),
    ("sau", "Gentamicina"): (0.08, 0.03, 0.04, 0.02),
    ("sau", "Oxacilina"): (0.22, 0.00, 0.06, 0.04),
    ("sau", "Vancomicina"): (0.005, 0.01, 0.00, 0.005),
}

# Tipos de muestra válidos (códigos del diccionario) y su frecuencia por especie.
MUESTRAS = {
    "eco": {"or": 0.45, "sa": 0.25, "ab": 0.10, "ha": 0.08, "es": 0.05, "br": 0.04, "ca": 0.03},
    "kpn": {"or": 0.30, "sa": 0.25, "es": 0.15, "br": 0.10, "tq": 0.08, "ab": 0.05, "ha": 0.04, "ca": 0.03},
    "pae": {"es": 0.30, "br": 0.20, "tq": 0.20, "sa": 0.10, "ha": 0.08, "or": 0.07, "ab": 0.05},
    "aba": {"es": 0.25, "br": 0.20, "tq": 0.15, "sa": 0.15, "ha": 0.10, "or": 0.08, "ab": 0.07},
    "sau": {"ha": 0.30, "sa": 0.20, "pi": 0.15, "as": 0.10, "ab": 0.08, "or": 0.07, "te": 0.05, "ca": 0.05},
}

# Localizaciones válidas (códigos del diccionario).
LOCALIZACIONES = {
    "in": 0.35,
    "out": 0.20,
    "eme": 0.15,
    "icu": 0.12,
    "int": 0.10,
    "inx": 0.08,
}

PREFIJOS = {
    "or": "URO",
    "sa": "SEC",
    "br": "BRO",
    "es": "ESP",
    "ha": "HER",
    "ab": "ABD",
    "ca": "CAT",
    "te": "TEJ",
    "tq": "TRA",
    "pi": "PIE",
    "as": "ABS",
}

DILUCIONES = [0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0]


def _cargar_metadatos_especies():
    """Devuelve {código: (nombre, grupo_general)} usando los diccionarios."""
    dicc = pd.read_excel(RUTA_DICCIONARIOS, usecols=["especie_3", "especie"]).dropna()
    codigo_a_nombre = dict(zip(dicc["especie_3"], dicc["especie"]))

    mapa = pd.read_excel(RUTA_MAPEO)
    nombre_a_grupo = dict(zip(mapa["Especie_especifica"], mapa["Grupo_general"]))

    metadatos = {}
    for codigo in ESPECIES:
        if codigo not in codigo_a_nombre:
            raise ValueError(f"Código de especie no encontrado en el diccionario: {codigo}")
        nombre = codigo_a_nombre[codigo]
        if nombre not in nombre_a_grupo:
            raise ValueError(f"Especie sin grupo general en el mapeo: {nombre}")
        metadatos[codigo] = (nombre, nombre_a_grupo[nombre])
    return metadatos


def _cargar_puntos_corte(metadatos):
    """Valida que cada combinación del panel tenga punto de corte CLSI clásico."""
    from datos.categorizacion import buscar_puntos_corte, cargar_puntos_corte_clsi

    _, clasico, _ = cargar_puntos_corte_clsi(RUTA_CLSI)
    puntos = {}
    for codigo, antibioticos in PANELES.items():
        nombre, grupo = metadatos[codigo]
        for antibiotico in antibioticos:
            pts = buscar_puntos_corte(clasico, antibiotico, nombre, grupo)
            if pts is None:
                raise ValueError(
                    f"Sin punto de corte CLSI para {nombre} / {antibiotico}"
                )
            puntos[(codigo, antibiotico)] = pts
    return puntos


def _elegir_categoria(rng, perfil, anio, mes):
    r_base, i_base, tendencia, amplitud = perfil
    probabilidad_r = r_base + tendencia * (anio - 2021)
    probabilidad_r += amplitud * np.sin(2 * np.pi * (mes - 1) / 12)
    probabilidad_r = float(np.clip(probabilidad_r, 0.01, 0.90))
    probabilidad_i = float(np.clip(i_base, 0.0, 0.10))
    if probabilidad_r + probabilidad_i > 0.95:
        probabilidad_i = max(0.0, 0.95 - probabilidad_r)

    valor = rng.random()
    if valor < probabilidad_r:
        return "R"
    if valor < probabilidad_r + probabilidad_i:
        return "I"
    return "S"


def _formatear_numero(valor):
    if abs(valor - round(valor)) < 1e-9:
        return str(int(round(valor)))
    texto = f"{valor:.4f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _elegir_mic(categoria, s, i, r, rng):
    """Devuelve un MIC en texto que vuelve a clasificar en la misma categoría."""
    if categoria == "S":
        candidatos = [d for d in DILUCIONES if d <= s]
        if not candidatos:
            candidatos = [s]
        cerca = candidatos[-3:]
        valor = float(cerca[int(rng.integers(0, len(cerca)))])
        prefijo = "<=" if rng.random() < 0.35 else ""
    elif categoria == "R":
        candidatos = [d for d in DILUCIONES if d >= r]
        if not candidatos:
            candidatos = [r]
        cerca = candidatos[:3]
        valor = float(cerca[int(rng.integers(0, len(cerca)))])
        prefijo = ">=" if rng.random() < 0.35 else ""
    else:
        if isinstance(i, (int, float)):
            valor = float(i)
        elif i == "rango":
            candidatos = [d for d in DILUCIONES if s < d < r]
            valor = (
                float(candidatos[int(rng.integers(0, len(candidatos)))])
                if candidatos
                else (s + r) / 2
            )
        else:
            valor = (s + r) / 2
        prefijo = ""
    return prefijo + _formatear_numero(valor)


def _elegir_muestra(rng, codigo):
    opciones = list(MUESTRAS[codigo])
    pesos = list(MUESTRAS[codigo].values())
    return str(rng.choice(opciones, p=pesos))


def _elegir_localizacion(rng):
    opciones = list(LOCALIZACIONES)
    pesos = list(LOCALIZACIONES.values())
    return str(rng.choice(opciones, p=pesos))


def generar_anio(anio, rng, puntos, contador):
    """Genera un DataFrame con todos los aislados sintéticos de un año."""
    codigos = list(ESPECIES)
    pesos = [ESPECIES[c]["peso"] for c in codigos]

    filas = []
    for mes in range(1, 13):
        n = int(rng.integers(140, 171))
        especies_mes = rng.choice(codigos, size=n, p=pesos)

        for codigo in especies_mes:
            muestra = _elegir_muestra(rng, codigo)
            localizacion = _elegir_localizacion(rng)
            edad = int(np.clip(rng.normal(ESPECIES[codigo]["edad_media"], 18), 0, 95))
            contador[0] += 1
            spec_num = f"{PREFIJOS.get(muestra, 'MUE')}{contador[0]:07d}"

            fila = {
                "fecha": date(anio, mes, int(rng.integers(1, 29))),
                "SPEC_NUM": spec_num,
                "Tipo de localizacion": localizacion,
                "Tipo de muestra": muestra,
                "Edad": edad,
                "especie": codigo,
            }
            for antibiotico in ANTIBIOTICOS:
                fila[antibiotico] = None

            for antibiotico in PANELES[codigo]:
                s, i, r = puntos[(codigo, antibiotico)]
                categoria = _elegir_categoria(
                    rng, PERFILES[(codigo, antibiotico)], anio, mes
                )
                fila[antibiotico] = _elegir_mic(categoria, s, i, r, rng)

            filas.append(fila)

    columnas = [
        "fecha",
        "SPEC_NUM",
        "Tipo de localizacion",
        "Tipo de muestra",
        "Edad",
        "especie",
    ] + ANTIBIOTICOS
    return pd.DataFrame(filas, columns=columnas).sort_values(
        ["fecha", "especie"], ignore_index=True
    )


def validar(rutas):
    """Ejecuta el pipeline real y comprueba que las predicciones son viables."""
    import shutil
    import tempfile

    import config
    from datos.categorizacion import procesar_categorizacion
    from datos.limpieza_final import procesar_limpieza_final
    from prediccion.preprocessing import cargar_datos, obtener_combinaciones_validas
    from sesion import dir_sesion

    procesados = []
    for ruta in rutas:
        df = pd.read_excel(ruta)
        categorizado, _, _, _, _, _ = procesar_categorizacion(df)
        limpio, _ = procesar_limpieza_final(categorizado)
        if any(c in limpio.columns for c in ("Hospital", "Region")):
            raise AssertionError(f"{ruta}: aparecieron columnas Hospital/Region")
        valores = pd.unique(limpio[ANTIBIOTICOS].values.ravel())
        permitidos = {"S", "I", "R", "Inconcluyente"}
        inesperados = {
            v for v in valores if pd.notna(v) and str(v) not in permitidos
        }
        if inesperados:
            raise AssertionError(f"{ruta}: valores no categorizados: {inesperados}")
        procesados.append((os.path.basename(ruta), limpio))

    # Guardar en una sesión temporal y usar el mismo cargador de la app.
    temp = tempfile.mkdtemp(prefix="sinteticos_validacion_")
    storage_original = config.STORAGE_ROOT
    try:
        config.STORAGE_ROOT = temp
        session_id = "validacion"
        base = dir_sesion(session_id)
        for nombre, limpio in procesados:
            anio = int(nombre.split("_")[1].split(".")[0])
            limpio.to_pickle(os.path.join(base, f"datos_{anio}.pkl"))

        largo = cargar_datos(session_id)
        combos, trimestres = obtener_combinaciones_validas(largo, minimo_trimestres=15)
    finally:
        config.STORAGE_ROOT = storage_original
        shutil.rmtree(temp, ignore_errors=True)

    print("\nValidación")
    print(f"  Filas totales procesadas: {sum(len(df) for _, df in procesados)}")
    print(f"  Combinaciones especie-antibiótico válidas: {len(combos)}")
    if combos.empty:
        raise AssertionError("No se generó ninguna combinación válida para predecir")
    print(f"  Trimestres consecutivos mínimos: {int(combos['trimestres_consecutivos_finales'].min())}")
    print(f"  Trimestres disponibles: {trimestres['trimestre'].nunique()}")
    print("  Muestra de combinaciones:")
    print(combos.head(10).to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desde", type=int, default=2021, help="Primer año (incluido)")
    parser.add_argument("--hasta", type=int, default=2025, help="Último año (incluido)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument(
        "--salida",
        default=SALIDA_POR_DEFECTO,
        help="Carpeta donde escribir los Excel",
    )
    parser.add_argument(
        "--validar",
        action="store_true",
        help="Ejecutar el pipeline real y comprobar las combinaciones válidas",
    )
    args = parser.parse_args()

    if args.desde > args.hasta:
        raise SystemExit("--desde no puede ser mayor que --hasta")

    metadatos = _cargar_metadatos_especies()
    puntos = _cargar_puntos_corte(metadatos)
    os.makedirs(args.salida, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    contador = [3_000_000]
    rutas = []
    for anio in range(args.desde, args.hasta + 1):
        df = generar_anio(anio, rng, puntos, contador)
        ruta = os.path.join(args.salida, f"datos_{anio}.xlsx")
        df.to_excel(ruta, index=False, engine="openpyxl")
        rutas.append(ruta)
        print(f"Generado {ruta} ({len(df)} filas)")

    print(f"\nListo: {len(rutas)} archivos en {args.salida}")
    if args.validar:
        validar(rutas)


if __name__ == "__main__":
    main()
