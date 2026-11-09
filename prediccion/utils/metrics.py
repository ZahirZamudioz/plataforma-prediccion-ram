import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error

def _calcular_mase(train, test, pred, m=1):

    mae = mean_absolute_error(test, pred)

    if len(train) <= m:
        return np.nan

    naive_mae = np.mean(
        np.abs(
            train.iloc[m:].values -
            train.iloc[:-m].values
        )
    )

    if naive_mae == 0:
        return np.nan

    return mae / naive_mae
