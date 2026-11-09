"""Reportes de procesamiento (HTML para el modal y Excel para descarga)."""
import os
import pickle
from io import BytesIO
from typing import Dict

import pandas as pd
import dash_bootstrap_components as dbc
from dash import html

from sesion import dir_sesion


def guardar_reporte(reporte: Dict, nombre_archivo: str, anio: int, session_id: str):
    """Persiste el reporte de procesamiento de un año en disco.

    Se guarda junto a datos_<año>.pkl en la carpeta de la sesión para que el
    reporte sobreviva a reinicios de la app y a los múltiples workers de gunicorn.
    """
    ruta = os.path.join(dir_sesion(session_id), f"reporte_{anio}.pkl")
    with open(ruta, "wb") as f:
        pickle.dump(
            {"reporte": reporte, "nombre_archivo": nombre_archivo, "anio": anio}, f
        )


def cargar_reporte(anio, session_id: str):
    """Carga el reporte persistido de un año; devuelve None si no existe."""
    if anio is None:
        return None
    ruta = os.path.join(dir_sesion(session_id), f"reporte_{anio}.pkl")
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def calcular_metricas_reporte(reporte: Dict) -> Dict:
    """Calcula totales de registros usando una unica fuente de verdad.

    `registros_eliminados` es el total real del pipeline (inicial - final).
    El desglose por motivo (aÃ±o / sin antibiÃ³ticos) es solo informativo.
    """
    total_inicial = reporte["total_registros_inicial"]
    elim_anio = reporte.get("registros_eliminados_anio", 0)
    elim_antibioticos = reporte.get("registros_eliminados_sin_antibioticos", 0)
    total_eliminados = reporte.get(
        "registros_eliminados", elim_anio + elim_antibioticos
    )
    return {
        "total_inicial": total_inicial,
        "total_eliminados": total_eliminados,
        "total_final": total_inicial - total_eliminados,
        "elim_anio": elim_anio,
        "elim_antibioticos": elim_antibioticos,
    }


# Colores Bootstrap usados por dbc.Progress (tema Flatly)
_COLOR_CONSERVADOS = "#28a745"
_COLOR_ELIM_ANIO = "#dc3545"
_COLOR_ELIM_ANTIBIOTICOS = "#ffc107"
_COLOR_ELIM_OTROS = "#6c757d"


def _secciones_barra_registros(m: Dict):
    """Segmentos apilados: verde (conservados) + rojos por motivo de eliminación."""
    total = m["total_inicial"]
    if total <= 0:
        return []

    pct_final = m["total_final"] / total * 100
    pct_anio = m["elim_anio"] / total * 100
    pct_antib = m["elim_antibioticos"] / total * 100
    pct_otros = max(0.0, m["total_eliminados"] - m["elim_anio"] - m["elim_antibioticos"]) / total * 100

    segmentos = [dbc.Progress(value=pct_final, color="success", bar=True)]
    if pct_anio > 0:
        segmentos.append(dbc.Progress(value=pct_anio, color="danger", bar=True))
    if pct_antib > 0:
        segmentos.append(dbc.Progress(value=pct_antib, color="warning", bar=True))
    if pct_otros > 0:
        segmentos.append(dbc.Progress(value=pct_otros, color="secondary", bar=True))
    return segmentos


def _leyenda_barra(m: Dict):
    total = m["total_inicial"] or 1

    def item(color, texto, valor):
        pct = valor / total * 100
        return html.Div([
            html.Span(" ", style={"display": "inline-block", "width": "14px", "height": "14px",
                                  "marginRight": "6px", "backgroundColor": color,
                                  "borderRadius": "3px"}),
            html.Span(f"{texto}: ", style={"fontWeight": "bold"}),
            html.Span(f"{valor} ({pct:.1f}%)"),
        ], style={"display": "inline-flex", "alignItems": "center", "marginRight": "16px"})

    items = [
        item(_COLOR_CONSERVADOS, "Conservados", m["total_final"]),
        item(_COLOR_ELIM_ANIO, "Eliminados por año no mayoritario", m["elim_anio"]),
        item(_COLOR_ELIM_ANTIBIOTICOS, "Eliminados sin punto de corte (CLSI)", m["elim_antibioticos"]),
    ]
    pct_otros = max(0, m["total_eliminados"] - m["elim_anio"] - m["elim_antibioticos"])
    if pct_otros > 0:
        items.append(item(_COLOR_ELIM_OTROS, "Eliminados por otros motivos", pct_otros))
    return html.Div(items, className="d-flex flex-wrap mt-2")


def generar_html_reporte(reporte: Dict, nombre_archivo: str, anio: int):

    m = calcular_metricas_reporte(reporte)

    def lista_resumida(items, max_mostrar=15):
        if not items:
            return [html.Li(html.Em("Ninguno"))]
        if len(items) > max_mostrar:
            return (
                [html.Li(item) for item in items[:max_mostrar]] +
                [html.Li(html.Em(f"... y {len(items)-max_mostrar} más (ver Excel completo)"))]
            )
        return [html.Li(item) for item in items]

    return html.Div([

        html.H4(f"{nombre_archivo} ({anio})"),
        html.Hr(),

        # ðŸ”¹ Resumen
        html.H5("Resumen de transformación de registros"),
        html.Div([
            dbc.Progress(_secciones_barra_registros(m)),
            _leyenda_barra(m),
        ], className="mb-3"),
        html.P([
            html.Strong("Registros (filas) iniciales: "), str(m["total_inicial"])
        ]),
        html.P([
            html.Strong("Registros (filas) finales: "), str(m["total_final"])
        ]),
        html.P([
            html.Strong("Registros (filas) eliminados: "), str(m["total_eliminados"])
        ]),

        html.Ul([
            html.Li(f"Registros de años no mayoritarios eliminados: {m['elim_anio']}"),
            html.Li(f"Registros sin puntos de corte (CLSI) eliminados: {m['elim_antibioticos']}")
        ]),

        html.Hr(),

        # ðŸ”¹ Columnas eliminadas
        html.H5("Columnas eliminadas"),
        html.Ul(lista_resumida(reporte["columnas_eliminadas"])),

        html.Br(),

        html.Hr(),

        # ðŸ”¹ Combinaciones sin punto de corte
        html.H5("Combinaciones especie-antibiótico sin punto de corte"),
        html.Ul(lista_resumida(reporte["combinaciones_sin_punto_corte"])),

        html.Hr(),
    ])


def generar_excel_reporte(reporte: Dict) -> bytes:
    """Genera el reporte en formato Excel y devuelve el contenido como bytes."""
    m = calcular_metricas_reporte(reporte)

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:

        # Hoja 1: Resumen
        resumen_df = pd.DataFrame({
            "Métrica": [
                "Registros iniciales",
                "Registros eliminados",
                "Registros finales"
            ],
            "Valor": [
                m["total_inicial"],
                m["total_eliminados"],
                m["total_final"]
            ]
        })
        resumen_df.to_excel(writer, sheet_name="Resumen", index=False)

        # Hoja 2: Columnas eliminadas (COMPLETO)
        pd.DataFrame({
            "Columnas eliminadas": reporte["columnas_eliminadas"]
        }).to_excel(writer, sheet_name="Columnas eliminadas", index=False)

        # Hoja 3: Combinaciones sin punto de corte (COMPLETO)
        pd.DataFrame({
            "Combinaciones sin punto de corte": reporte["combinaciones_sin_punto_corte"]
        }).to_excel(writer, sheet_name="Sin punto de corte", index=False)

    buffer.seek(0)
    return buffer.read()
