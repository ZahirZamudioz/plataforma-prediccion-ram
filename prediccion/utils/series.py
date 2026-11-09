import pandas as pd

# ==========================================================
# CONSTRUIR SERIE TEMPORAL
# ==========================================================

def _construir_serie(
    df_long,
    df_trimestres_finales,
    especie,
    antibiotico
):
    """
    Construye la serie trimestral de proporción de resistencia
    utilizando únicamente los trimestres consecutivos finales
    definidos en preprocessing.py.
    """

    # Filtrar combinación

    df = df_long[
        (df_long["especie"] == especie)
        &
        (df_long["antibiotico"] == antibiotico)
    ].copy()

    # Eliminar resultados intermedios

    df = df[df["resultado"].isin(["R", "S"])]

    # Variable binaria

    df["R_bin"] = (df["resultado"] == "R").astype(int)

    # Crear trimestre

    df["trimestre"] = (
        pd.to_datetime(df["fecha"])
        .dt.to_period("Q")
    )

    # Trimestres válidos para esta combinación

    trims = df_trimestres_finales[
        (df_trimestres_finales["especie"] == especie)
        &
        (df_trimestres_finales["antibiotico"] == antibiotico)
    ][["trimestre"]]

    # Conservar únicamente esos trimestres

    df = df.merge(
        trims,
        on="trimestre",
        how="inner"
    )

    # Agrupar

    serie = (
        df
        .groupby("trimestre")
        .agg(
            resistentes=("R_bin", "sum"),
            total=("R_bin", "count")
        )
    )

    # Proporción

    serie["prop_R"] = (
        serie["resistentes"] /
        serie["total"]
    )

    serie = serie.sort_index()

    return df, serie
