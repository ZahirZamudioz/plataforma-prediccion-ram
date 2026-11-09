import numpy as np
import pandas as pd
from prediccion.utils.series import _construir_serie
from prediccion.utils.metrics import _calcular_mase

from sklearn.metrics import mean_squared_error, mean_absolute_error

from statsmodels.tsa.statespace.sarimax import SARIMAX

from pmdarima import auto_arima


# ==========================================================
# ENTRENAMIENTO
# ==========================================================

def entrenar_arima(
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
    # Train / Test
    # ------------------------------------------------------

    train = serie.iloc[:-4]

    test = serie.iloc[-4:]

    # ------------------------------------------------------
    # AutoARIMA
    # ------------------------------------------------------

    auto_model = auto_arima(
        train,
        seasonal=False,
        trace=False,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore"
    )

    # ------------------------------------------------------
    # Modelo ARIMA
    # ------------------------------------------------------

    modelo = SARIMAX(
        train,
        order=auto_model.order,
        seasonal_order=(0,0,0,0),
        enforce_stationarity=False,
        enforce_invertibility=False

    )
    resultado = modelo.fit(disp=False)

    # ------------------------------------------------------
    # Predicción
    # ------------------------------------------------------

    pred = resultado.forecast(steps=4)

    # ------------------------------------------------------
    # Métricas
    # ------------------------------------------------------

    rmse = np.sqrt(
        mean_squared_error(
            test,
            pred
        )
    )

    mae = mean_absolute_error(
        test,
        pred
    )

    mase = _calcular_mase(
        train,
        test,
        pred,
        m=1
    )

    # ------------------------------------------------------
    # Resultados
    # ------------------------------------------------------

    return {
        "serie": serie_df,
        "train": train,
        "test": test,
        "predicciones": pred,
        "modelo": resultado,
        "metricas": {
            "especie": especie,
            "antibiotico": antibiotico,
            "modelo": "ARIMA",
            "order": str(auto_model.order),
            "rmse": rmse,
            "mae": mae,
            "mase": mase
        }
    }


# ==========================================================
# PREDICCIÓN FUTURA
# ==========================================================

def predecir_arima(
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

    auto_model = auto_arima(
        serie,
        seasonal=False,
        trace=False,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore"
    )

    modelo = SARIMAX(
        serie,
        order=auto_model.order,
        seasonal_order=(0, 0, 0, 0),
        enforce_stationarity=False,
        enforce_invertibility=False
    )

    resultado = modelo.fit(disp=False)

    pred = resultado.forecast(steps=4)

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
        "valor": pred.values,
        "tipo": "prediccion"
    })

    return pd.concat([historico, futuro], ignore_index=True)
