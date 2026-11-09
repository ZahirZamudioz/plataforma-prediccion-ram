"""Punto de entrada de la plataforma: app Dash, server (gunicorn) y pestañas globales."""
import os
import secrets

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import dash_bootstrap_components as dbc
from dash import Dash, callback, dcc, html, Input, Output, State

from datos.gestor_datos import obtener_anios_disponibles, cargar_datos
from datos.transformaciones import (
    calcular_conteos_porcentajes,
    transformar_datos_para_aislados_barras,
    transformar_datos_para_heatmap,
    trasformar_datos_tipo_de_servicio,
    transformar_datos_para_frecuencia_tipo_muestra,
    transformar_datos_para_edad,
    transformar_datos_para_muestras_por_servicio,
    transformar_datos_para_especies_por_muestra,
)
from graficos.monitoreo import (
    crear_fig_aislados,
    crear_heatmap_resistencia,
    crear_fig_localizacion,
    construir_tabla,
    construir_tabla_localizacion,
    crear_fig_muestra,
    construir_tabla_muestra,
    crear_fig_edad,
    crear_fig_servicio_muestras,
    construir_tabla_servicio_muestras,
    crear_fig_muestra_especies,
    construir_tabla_muestra_especies,
)
from reportes.reportes import generar_html_reporte, generar_excel_reporte
from config import COLORES_ESPECIES, ESPECIES_FIJAS, MESES
from layout.muestras import layout_muestras
from layout.aislados import layout_aislados
from layout.reporte import (
    upload_section,
    gestion_datos,
    modal_reporte,
    modal_confirmar_eliminacion,
    download_reporte,
)
from prediccion.layout.prediccion import layout_prediccion
from prediccion.resultados import cargar_resultados
from sesion import obtener_session_id

# --- CONFIGURACIONES GLOBALES ---
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        dbc.icons.FONT_AWESOME,
        "https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;500;700&display=swap",
    ],
    suppress_callback_exceptions=True,
)
server = app.server   # servidor WSGI expuesto para despliegues

# Clave para firmar la cookie de sesión (anónima). En producción se recomienda
# definir la variable de entorno SECRET_KEY para mantener las sesiones estables
# entre reinicios; si no existe, se genera una clave aleatoria temporal.
server.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
server.config["SESSION_COOKIE_SAMESITE"] = "Lax"


@server.before_request
def _asegurar_sesion():
    """Garantiza que el navegador tenga cookie de sesión antes de los callbacks."""
    obtener_session_id()

# Fondo blanco en el área de los gráficos (sin tocar colores de las series)
pio.templates.default = "plotly_white"

# --- HELPERS ---
def generar_orden_meses(anio):
    return [f"{mes}-{anio}" for mes in MESES]


def figura_vacia(mensaje="Sin datos para este año"):
    return go.Figure().add_annotation(text=mensaje, showarrow=False)


# --- ORQUESTADOR DE VISUALIZACIONES (puro, sin estado global) ---
def generar_visualizaciones(df, anio):
    """Calcula todas las figuras y tablas para un DataFrame de un año."""
    orden_meses = generar_orden_meses(anio)

    # ------- TRANSFORMACIONES DE DATOS -------
    count_table = calcular_conteos_porcentajes(df)
    df_grafLineas = count_table[count_table['total'] >= 10].copy()
    df_grafLineas["fecha"] = pd.Categorical(df_grafLineas["fecha"], categories=orden_meses, ordered=True)
    antibioticos = sorted(df_grafLineas["antibiotico"].dropna().unique())

    conteo_especies, orden_especies = transformar_datos_para_aislados_barras(df)

    (pivots_positivas, pivots_negativas) = transformar_datos_para_heatmap(count_table, conteo_especies)

    (pivot_R_pos, pivot_S_pos, pivot_I_pos, pivot_Inconcluyente_pos,
     pivot_R_count_pos, pivot_S_count_pos, pivot_I_count_pos, pivot_Inconcluyente_count_pos) = pivots_positivas

    (pivot_R_neg, pivot_S_neg, pivot_I_neg, pivot_Inconcluyente_neg,
     pivot_R_count_neg, pivot_S_count_neg, pivot_I_count_neg, pivot_Inconcluyente_count_neg) = pivots_negativas

    conteo_servicio, conteo_servicio_tabla, df_unicos = trasformar_datos_tipo_de_servicio(df)

    conteo_muestra, conteo_muestra_tabla = transformar_datos_para_frecuencia_tipo_muestra(df_unicos)

    conteo_edad = transformar_datos_para_edad(df_unicos)

    conteo_servicio_muestras, orden_servicios, orden_tipos_muestra, muestras_infrecuentes = transformar_datos_para_muestras_por_servicio(df_unicos)

    conteo_muestra_especies, orden_muestras, orden_de_especies = transformar_datos_para_especies_por_muestra(df, muestras_infrecuentes)

    # ------- GENERACIÓN DE GRÁFICOS -------
    fig3 = crear_fig_aislados(conteo_especies, orden_especies)

    fig_heatmap_pos = crear_heatmap_resistencia(
        pivot_R_pos, pivot_S_pos, pivot_I_pos, pivot_Inconcluyente_pos,
        pivot_R_count_pos, pivot_S_count_pos, pivot_I_count_pos, pivot_Inconcluyente_count_pos,
        yaxis_title="Especie (Gram Positiva)"
    )

    fig_heatmap_neg = crear_heatmap_resistencia(
        pivot_R_neg, pivot_S_neg, pivot_I_neg, pivot_Inconcluyente_neg,
        pivot_R_count_neg, pivot_S_count_neg, pivot_I_count_neg, pivot_Inconcluyente_count_neg,
        yaxis_title="Especie (Gram Negativa)"
    )

    fig_localizacion = crear_fig_localizacion(conteo_servicio)
    tabla_localizacion = construir_tabla_localizacion(conteo_servicio_tabla)

    fig_muestra = crear_fig_muestra(conteo_muestra)
    tabla_muestra = construir_tabla_muestra(conteo_muestra_tabla)

    fig_edad = crear_fig_edad(conteo_edad)

    fig_servicio_muestras = crear_fig_servicio_muestras(conteo_servicio_muestras, orden_servicios, orden_tipos_muestra)
    tabla_servicio_muestras = construir_tabla_servicio_muestras(conteo_servicio_muestras)

    fig_muestra_especies = crear_fig_muestra_especies(conteo_muestra_especies, orden_muestras, orden_de_especies)
    tabla_muestra_especies = construir_tabla_muestra_especies(conteo_muestra_especies)

    return {
        "fig_localizacion": fig_localizacion,
        "tabla_localizacion": tabla_localizacion,
        "fig_muestra": fig_muestra,
        "tabla_muestra": tabla_muestra,
        "fig_edad": fig_edad,
        "fig_servicio_muestras": fig_servicio_muestras,
        "tabla_servicio_muestras": tabla_servicio_muestras,
        "fig_muestra_especies": fig_muestra_especies,
        "tabla_muestra_especies": tabla_muestra_especies,
        "fig3": fig3,
        "fig_heatmap_pos": fig_heatmap_pos,
        "fig_heatmap_neg": fig_heatmap_neg,
        "antibioticos": antibioticos,
    }


# Memoización por (sesión, año): evita recalcular todo al cambiar de pestaña
# (solo se invalida al subir/borrar datos).
_cache_visualizaciones = {}


def obtener_visualizaciones(df, anio, session_id):
    key = (session_id, anio)
    if key not in _cache_visualizaciones:
        _cache_visualizaciones[key] = generar_visualizaciones(df, anio)
    return _cache_visualizaciones[key]


def invalidar_visualizaciones(anio, session_id):
    _cache_visualizaciones.pop((session_id, anio), None)


def visualizaciones_vacias():
    """Placeholders para cuando no hay datos del año seleccionado."""
    def tabla_vacia(tabla_id):
        return construir_tabla(tabla_id, [], [])
    return {
        "fig_localizacion": figura_vacia(), "tabla_localizacion": tabla_vacia("tabla_localizacion"),
        "fig_muestra": figura_vacia(), "tabla_muestra": tabla_vacia("tabla_muestra"),
        "fig_edad": figura_vacia(),
        "fig_servicio_muestras": figura_vacia(), "tabla_servicio_muestras": tabla_vacia("tabla_servicio_muestras"),
        "fig_muestra_especies": figura_vacia(), "tabla_muestra_especies": tabla_vacia("tabla_muestra_especies"),
        "fig3": figura_vacia(), "fig_heatmap_pos": figura_vacia(), "fig_heatmap_neg": figura_vacia(),
        "antibioticos": [],
    }


# --- LAYOUT DE LA APP ---
app.layout = dbc.Container([
    html.Div([
        dbc.Row([
            dbc.Col(html.I(className="fas fa-microscope"), width="auto"),
            dbc.Col([
                html.H1("Plataforma para el monitoreo de resistencia antimicrobiana",
                        className="app-title"),
                html.P("Análisis de muestras, aislados y predicción de resistencia antimicrobiana",
                       className="app-subtitle"),
            ], width=True),
        ], align="center", className="g-3 m-0"),
    ], className="app-header mb-4"),
    # Nueva fila para pestañas y dropdown de años
    dbc.Row([
        dbc.Col(
            dbc.Tabs([
                dbc.Tab(label="Muestras analizadas", tab_id="tab-muestras",
                        label_class_name="tab-icon tab-muestras"),
                dbc.Tab(label="Aislados analizados", tab_id="tab-aislados",
                        label_class_name="tab-icon tab-aislados"),
                dbc.Tab(label="Predicción", tab_id="tab-prediccion",
                        label_class_name="tab-icon tab-prediccion"),
                dbc.Tab(label="Cargar Datos", tab_id="tab-cargar",
                        children=html.Div([upload_section, gestion_datos]),
                        label_class_name="tab-icon tab-cargar")
            ], id="tabs", active_tab="tab-muestras", class_name="mb-3"),
            width=8
        ),
        dbc.Col(
            html.Div([
                html.Div([
                    html.Label("Seleccionar año:", className="me-2"),
                    dcc.Dropdown(
                        id="year-selector",
                        options=[],
                        value=None,
                        clearable=False,
                        style={"width": "150px"}
                    )
                ], style={"display": "flex", "alignItems": "center"}, id="year-selector-container"),
            ], style={"display": "flex", "justifyContent": "flex-end"}),
            width=4,
        )
    ], className="mb-3"),

    html.Div(id="tab-content"),

    # ────────────────────────────────────────────────
    #          MODAL DE REPORTE
    # ────────────────────────────────────────────────
    modal_reporte,

    modal_confirmar_eliminacion,

    dcc.Store(id="eliminar-objetivo"),
    dcc.Store(id="reporte-objetivo"),

    download_reporte,
], fluid=True, class_name="px-2")


@app.callback(
    Output("year-selector-container", "style"),
    Input("tabs", "active_tab"),
)
def toggle_globales(active_tab):
    """Oculta el selector de año en las pestañas que no lo necesitan."""
    ocultar_year = active_tab in ("tab-prediccion", "tab-cargar")
    return {"display": "none"} if ocultar_year else {"display": "flex", "alignItems": "center"}


# --- CALLBACKS ---
@app.callback(
    Output("year-selector", "options", allow_duplicate=True),
    Output("year-selector", "value", allow_duplicate=True),
    Input("tabs", "active_tab"),
    State("year-selector", "value"),
    prevent_initial_call=True,
)
def inicializar_selector_anio(active_tab, valor_actual):
    """Carga los años de la sesión al abrir la página y al cambiar de pestaña."""
    anios = obtener_anios_disponibles(obtener_session_id())
    opciones = [{"label": str(y), "value": y} for y in anios]
    if valor_actual in anios:
        return opciones, valor_actual
    return opciones, (max(anios) if anios else None)


@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("year-selector", "value")
)
def render_tab_content(active_tab, selected_year):
    session_id = obtener_session_id()
    df = cargar_datos(selected_year, session_id) if selected_year else None
    if df is None or df.empty:
        vis = visualizaciones_vacias()
    else:
        vis = obtener_visualizaciones(df, selected_year, session_id)

    if active_tab == "tab-muestras":
        return layout_muestras(
            vis["fig_localizacion"], vis["tabla_localizacion"],
            vis["fig_muestra"], vis["tabla_muestra"],
            vis["fig_edad"],
            vis["fig_servicio_muestras"], vis["tabla_servicio_muestras"],
            vis["fig_muestra_especies"], vis["tabla_muestra_especies"],
        )

    if active_tab == "tab-aislados":
        return layout_aislados(
            vis["fig3"], vis["fig_heatmap_pos"], vis["fig_heatmap_neg"], vis["antibioticos"]
        )

    if active_tab == "tab-prediccion":
        _, ganadores = cargar_resultados(session_id)
        return layout_prediccion(ganadores)


# Registrar callbacks de las pestañas (los decoradores se ejecutan al importar)
from callbacks.aislados import registrar as registrar_aislados
from callbacks.carga import registrar as registrar_carga
from prediccion.callbacks.prediccion import registrar as registrar_prediccion

registrar_aislados(app, generar_orden_meses, figura_vacia)
registrar_carga(app, invalidar_visualizaciones)
registrar_prediccion(app)


if __name__ == "__main__":
    app.run(debug=os.getenv("DASH_DEBUG") == "1", port=8053)
