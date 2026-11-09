"""Identidad y rutas de almacenamiento por sesión (anónima, por navegador).

El id de sesión vive en la cookie de Flask (persistente). Todos los datos de
usuario se guardan bajo STORAGE_ROOT/<session_id>/, de modo que cada navegador
tiene su propio conjunto de años y reportes.
"""
import os
import uuid

from flask import session

import config


def obtener_session_id() -> str:
    """Devuelve el id de sesión del navegador, creándolo si no existe.

    Usa la cookie de sesión de Flask (persistente). Fuera de un contexto de
    request (p. ej. scripts offline) cae a la variable de entorno SESSION_ID
    o a "default".
    """
    try:
        sid = session.get("sid")
        if not sid:
            sid = uuid.uuid4().hex
            session["sid"] = sid
            session.permanent = True
        return sid
    except RuntimeError:
        return os.getenv("SESSION_ID", "default")


def dir_sesion(session_id: str) -> str:
    """Carpeta de almacenamiento de una sesión (la crea si no existe)."""
    ruta = os.path.join(config.STORAGE_ROOT, session_id)
    os.makedirs(ruta, exist_ok=True)
    return ruta


def dir_resultados(session_id: str) -> str:
    """Carpeta de resultados de predicción de una sesión (la crea si no existe)."""
    ruta = os.path.join(dir_sesion(session_id), "resultados")
    os.makedirs(ruta, exist_ok=True)
    return ruta
