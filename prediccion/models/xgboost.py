import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

from prediccion.utils.series import _construir_serie
from prediccion.utils.metrics import _calcular_mase


# ==========================================================
# ENTRENAMIENTO
# ==========================================================

def entrenar_xgboost(
    df_long,
    df_trimestres_finales,
    especie,
    antibiotico
):

    # ------------------------------------------------------
    # Serie temporal
    # ------------------------------------------------------

    _, serie_df = _construir_serie(
        df_long,
        df_trimestres_finales,
        especie,
        antibiotico
    )

    # ------------------------------------------------------
    # Serie de proporciones
    # ------------------------------------------------------

    serie = serie_df["prop_R"]

    # ------------------------------------------------------
    # Crear features
    # ------------------------------------------------------

    df_xgb = serie_df[["prop_R"]].copy()

    df_xgb["lag1"] = df_xgb["prop_R"].shift(1)
    df_xgb["lag2"] = df_xgb["prop_R"].shift(2)
    df_xgb["lag3"] = df_xgb["prop_R"].shift(3)
    df_xgb["lag4"] = df_xgb["prop_R"].shift(4)

    df_xgb["time_idx"] = range(len(df_xgb))

    df_xgb["quarter"] = df_xgb.index.quarter

    df_xgb = df_xgb.dropna().reset_index(drop=True)

    features = ["lag1", "lag2", "lag3", "lag4", "quarter", "time_idx"]

    X = df_xgb[features]
    y = df_xgb["prop_R"]

    # ------------------------------------------------------
    # Train / Test
    # ------------------------------------------------------

    n_test = 4

    X_train = X.iloc[:-n_test]
    X_test = X.iloc[-n_test:]

    y_train = y.iloc[:-n_test]
    y_test = y.iloc[-n_test:]

    # ------------------------------------------------------
    # Modelo
    # ------------------------------------------------------

    modelo = XGBRegressor(
        n_estimators=50,
        max_depth=2,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42
    )

    modelo.fit(X_train, y_train)

    # ------------------------------------------------------
    # Predicción
    # ------------------------------------------------------

    pred = modelo.predict(X_test)

    # ------------------------------------------------------
    # Métricas
    # ------------------------------------------------------

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            pred
        )
    )

    mae = mean_absolute_error(
        y_test,
        pred
    )

    mase = _calcular_mase(
        serie.iloc[:-n_test],
        y_test,
        pred,
        m=1
    )

    # ------------------------------------------------------
    # Resultados
    # ------------------------------------------------------

    return {
        "serie": serie_df,
        "train": y_train,
        "test": y_test,
        "predicciones": pred,
        "modelo": modelo,
        "metricas": {
            "especie": especie,
            "antibiotico": antibiotico,
            "modelo": "XGBoost",
            "rmse": rmse,
            "mae": mae,
            "mase": mase
        }
    }


# ==========================================================
# PREDICCIÓN FUTURA
# ==========================================================

def _crear_features(lags, time_idx, quarter):
    """Crea el vector de features para XGBoost."""

    return pd.DataFrame([{
        "lag1": lags[-1],
        "lag2": lags[-2],
        "lag3": lags[-3],
        "lag4": lags[-4],
        "quarter": quarter,
        "time_idx": time_idx,
    }])


def predecir_xgboost(
    df_long,
    df_trimestres_finales,
    especie,
    antibiotico
):

    _, serie_df = _construir_serie(
        df_long,
        df_trimestres_finales,
        especie,
        antibiotico
    )

    serie = serie_df["prop_R"]

    df_xgb = serie_df[["prop_R"]].copy()

    df_xgb["lag1"] = df_xgb["prop_R"].shift(1)
    df_xgb["lag2"] = df_xgb["prop_R"].shift(2)
    df_xgb["lag3"] = df_xgb["prop_R"].shift(3)
    df_xgb["lag4"] = df_xgb["prop_R"].shift(4)

    df_xgb["time_idx"] = range(len(df_xgb))

    df_xgb["quarter"] = df_xgb.index.quarter

    df_xgb = df_xgb.dropna().reset_index(drop=True)

    features = ["lag1", "lag2", "lag3", "lag4", "quarter", "time_idx"]

    X = df_xgb[features]
    y = df_xgb["prop_R"]

    modelo = XGBRegressor(
        n_estimators=50,
        max_depth=2,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42
    )

    modelo.fit(X, y)

    valores = serie.values.tolist()

    lags = valores[-4:]

    time_idx_base = len(serie)

    quarter_base = serie.index[-1].quarter

    predicciones = []

    for i in range(4):

        quarter = quarter_base + i + 1

        if quarter > 4:
            quarter = quarter - 4

        features_row = _crear_features(
            lags, time_idx_base + i, quarter
        )

        pred = modelo.predict(features_row)[0]

        predicciones.append(pred)

        lags = lags[1:] + [pred]

    historico = pd.DataFrame({
        "trimestre": serie.index.astype(str),
        "valor": serie.values,
        "tipo": "observado"
    })

    futuro_idx = pd.period_range(
        start=serie.index[-1] + 1,
        periods=4,
        freq="Q"
    )

    futuro = pd.DataFrame({
        "trimestre": futuro_idx.astype(str),
        "valor": predicciones,
        "tipo": "prediccion"
    })

    return pd.concat([historico, futuro], ignore_index=True)
