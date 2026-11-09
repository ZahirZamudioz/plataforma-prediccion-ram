"""Lectura/escritura de los pickles de resultados de predicción (sin ML).

Importar este módulo NO carga las librerías pesadas (tensorflow, xgboost, etc.),
por eso puede usarse al arrancar la app y dentro de los callbacks.
"""
import os

import pandas as pd

from sesion import dir_resultados


def guardar_resultados(predicciones, ganadores, session_id):
    """Persiste los pickles de predicción y ganadores en la carpeta de la sesión."""
    carpeta = dir_resultados(session_id)
    predicciones.to_pickle(os.path.join(carpeta, "predicciones.pkl"))
    ganadores.to_pickle(os.path.join(carpeta, "ganadores.pkl"))


def cargar_resultados(session_id):
    """Carga (predicciones, ganadores) de la sesión; (None, None) si no existen."""
    carpeta = dir_resultados(session_id)
    ruta_predicciones = os.path.join(carpeta, "predicciones.pkl")
    ruta_ganadores = os.path.join(carpeta, "ganadores.pkl")

    if not (os.path.exists(ruta_predicciones) and os.path.exists(ruta_ganadores)):
        return None, None

    return pd.read_pickle(ruta_predicciones), pd.read_pickle(ruta_ganadores)
