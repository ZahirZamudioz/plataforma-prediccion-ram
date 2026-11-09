"""Preprocesamiento para predicción: formato largo a partir de los pickles de data/."""
import os

import pandas as pd

from sesion import dir_sesion


MESES = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12,
}


def _parsear_fecha(valor):
    """Convierte 'Junio-2021' (o un Timestamp ya parseado) a Timestamp a nivel mes."""
    if isinstance(valor, (pd.Timestamp, pd.DatetimeIndex)):
        return valor
    try:
        mes, anio = str(valor).strip().split("-")
        return pd.Timestamp(year=int(anio), month=MESES[mes.strip()], day=1)
    except Exception:
        return pd.NaT


def cargar_datos(session_id):
    """
    Carga los pickles procesados de la sesión (un DataFrame por año) y los
    convierte a formato largo con las columnas:
        fecha, especie, antibiotico, resultado

    La columna 'fecha' viene como 'Junio-2021' en los pickles; se convierte
    a Timestamp a nivel mes (suficiente para el pipeline trimestral).
    """
    base = dir_sesion(session_id)
    archivos = sorted(
        f for f in os.listdir(base)
        if f.startswith("datos_") and f.endswith(".pkl")
    )

    if not archivos:
        raise FileNotFoundError(f"No se encontraron pickles de datos en {base}")

    dataframes = [pd.read_pickle(os.path.join(base, f)) for f in archivos]
    df = pd.concat(dataframes, ignore_index=True)

    df["fecha"] = df["fecha"].map(_parsear_fecha)
    df = df.dropna(subset=["fecha"])

    columnas_fijas = [
        "fecha",
        "SPEC_NUM",
        "Tipo de localizacion",
        "Tipo de muestra",
        "Edad",
        "especie",
        "Grupo_general",
        "Grupo_principal"
    ]

    # Metadatos heredados de versiones anteriores: no se crean ni se usan, pero
    # se ignoran si aparecen en pickles antiguos para que no se traten como
    # antibióticos.
    columnas_heredadas = {"Region", "Hospital"}

    columnas_antibioticos = [
        c for c in df.columns
        if c not in columnas_fijas and c not in columnas_heredadas
    ]

    df_long = df.melt(
        id_vars=["fecha", "especie"],
        value_vars=columnas_antibioticos,
        var_name="antibiotico",
        value_name="resultado"
    )

    df_long = df_long.dropna(subset=["resultado"])

    return df_long


def contar_trimestres_finales(fila):

    contador = 0

    for valor in fila.to_numpy()[::-1]:

        if valor:
            contador += 1
        else:
            break

    return contador


def obtener_combinaciones_validas(df_long, minimo_trimestres=15):
    """
    Identifica las combinaciones especie-antibiótico que poseen
    al menos 'minimo_trimestres' consecutivos válidos al final
    de la serie. Un trimestre es válido cuando tiene datos en al menos
    dos meses diferentes.
    """

    # --------------------------------------------------------

    df_mes = (
        df_long
        .assign(
            mes=lambda x: x["fecha"].dt.to_period("M")
        )
        .groupby(
            ["especie", "antibiotico", "mes"]
        )
        .size()
        .reset_index(name="n")
    )

    # Definición del trimestre

    df_mes["trimestre"] = (
        df_mes["mes"]
        .dt.to_timestamp()
        .dt.to_period("Q")
    )

    # Número de meses presentes en esos trimestres

    df_trim = (
        df_mes
        .groupby(
            ["especie", "antibiotico", "trimestre"]
        )
        .agg(
            meses_presentes=("mes", "nunique")
        )
        .reset_index()
    )

    df_trim["trimestre_valido"] = (
        df_trim["meses_presentes"] >= 2
    )

    # --------------------------------------------------------

    matriz = (
    df_trim
    .pivot_table(
        index=["especie", "antibiotico"],
        columns="trimestre",
        values="trimestre_valido"
    )
    .fillna(False)
    .infer_objects(copy=False)
    .reset_index()
    )

    columnas_trim = sorted(
    [c for c in matriz.columns if isinstance(c, pd.Period)]
    )

    columnas_trim = sorted(columnas_trim)

    # --------------------------------------------------------

    matriz["trimestres_consecutivos_finales"] = (
        matriz[columnas_trim]
        .apply(contar_trimestres_finales, axis=1)
    )

    # --------------------------------------------------------

    combinaciones_validas = (
        matriz[
            [
                "especie",
                "antibiotico",
                "trimestres_consecutivos_finales"
            ]
        ]
        .query(
            "trimestres_consecutivos_finales >= @minimo_trimestres"
        )
        .sort_values(
            "trimestres_consecutivos_finales",
            ascending=False
        )
        .reset_index(drop=True)
    )

    filas = []

    for _, fila in combinaciones_validas.iterrows():

        especie = fila["especie"]
        antibiotico = fila["antibiotico"]
        n = fila["trimestres_consecutivos_finales"]

        fila_matriz = matriz.loc[
            (matriz["especie"] == especie)
            &
            (matriz["antibiotico"] == antibiotico)
        ].iloc[0]

        trimestres = columnas_trim[-n:]

        for trimestre in trimestres:

            filas.append(
                {
                    "especie": especie,
                    "antibiotico": antibiotico,
                    "trimestre": trimestre
                }
            )

    df_trimestres_finales = pd.DataFrame(filas)

    return combinaciones_validas, df_trimestres_finales
