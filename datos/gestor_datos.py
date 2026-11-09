import os
import pickle

import pandas as pd

from datos.categorizacion import procesar_categorizacion
from datos.limpieza_final import procesar_limpieza_final
from sesion import dir_sesion


# Caché en memoria de DataFrames cargados por (session_id, anio)
_carga_cache = {}


def procesar_archivo_subido(contenido, anio, session_id):
    # Convertir contenido a DataFrame
    df = pd.read_excel(pd.ExcelFile(pd.io.common.BytesIO(contenido)))

    total_inicial = len(df)

    # Procesar con Categorizacion.py
    data_categorizado, _, _, _, _, reporte = procesar_categorizacion(df)

    # Procesar con LimpiezaFinal.py
    data_limpia, reporte_limpieza = procesar_limpieza_final(data_categorizado)
    total_final = len(data_limpia)

    eliminados_reales = total_inicial - total_final

    # Actualizar reporte con datos reales
    reporte["total_registros_inicial"] = total_inicial
    reporte["registros_eliminados"] = eliminados_reales
    reporte["registros_eliminados_anio"] = reporte_limpieza["registros_eliminados_anio"]
    reporte["registros_eliminados_sin_antibioticos"] = reporte_limpieza["registros_eliminados_sin_antibioticos"]
    reporte["columnas_antibioticos_vacias"] = reporte_limpieza["columnas_antibioticos_vacias"]

    # Guardar DataFrame procesado
    guardar_datos(data_limpia, anio, session_id)

    return data_limpia, reporte


def guardar_datos(df, anio, session_id):
    archivo = os.path.join(dir_sesion(session_id), f'datos_{anio}.pkl')
    with open(archivo, 'wb') as f:
        pickle.dump(df, f)
    _carga_cache[(session_id, anio)] = df  # actualizar caché para que el dashboard vea los datos nuevos


def cargar_datos(anio, session_id):
    key = (session_id, anio)
    if key in _carga_cache:
        return _carga_cache[key]
    archivo = os.path.join(dir_sesion(session_id), f'datos_{anio}.pkl')
    if os.path.exists(archivo):
        with open(archivo, 'rb') as f:
            df = pickle.load(f)
        _carga_cache[key] = df
        return df
    return None


def obtener_anios_disponibles(session_id):
    base = dir_sesion(session_id)
    archivos = [f for f in os.listdir(base) if f.startswith('datos_') and f.endswith('.pkl')]
    anios = [int(f.split('_')[1].split('.')[0]) for f in archivos]
    return sorted(anios)


def eliminar_datos(anio, session_id):
    """Elimina los datos y el reporte de un año. Devuelve True si borró algo."""
    anio = int(anio)
    base = dir_sesion(session_id)
    borrado = False
    for nombre in (f'datos_{anio}.pkl', f'reporte_{anio}.pkl'):
        archivo = os.path.join(base, nombre)
        if os.path.exists(archivo):
            os.remove(archivo)
            borrado = True
    _carga_cache.pop((session_id, anio), None)
    return borrado


def eliminar_todos_datos(session_id):
    """Elimina todos los datos y reportes cargados. Devuelve los años borrados."""
    base = dir_sesion(session_id)
    borrados = []
    for archivo in os.listdir(base):
        if (archivo.startswith('datos_') or archivo.startswith('reporte_')) and archivo.endswith('.pkl'):
            try:
                anio = int(archivo.split('_')[1].split('.')[0])
            except (IndexError, ValueError):
                continue
            if anio not in borrados:
                borrados.append(anio)
            os.remove(os.path.join(base, archivo))
            _carga_cache.pop((session_id, anio), None)
    return sorted(borrados)


def obtener_anios_con_reporte(session_id):
    """Devuelve una lista ordenada de años que tienen reporte guardado (reporte_*.pkl)"""
    base = dir_sesion(session_id)
    anios = []
    for f in os.listdir(base):
        if f.startswith('reporte_') and f.endswith('.pkl'):
            try:
                anios.append(int(f.split('_')[1].split('.')[0]))
            except (IndexError, ValueError):
                continue
    return sorted(anios)
