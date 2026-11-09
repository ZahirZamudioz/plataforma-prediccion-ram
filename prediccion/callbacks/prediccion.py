"""Callbacks de la pestaña de predicción."""
import dash
import plotly.graph_objects as go
from dash import Input, Output

from prediccion.generacion import iniciar_generacion, leer_estado, presentacion
from prediccion.graficos.prediccion import figura_prediccion
from prediccion.resultados import cargar_resultados
from sesion import obtener_session_id


def registrar(app):
    """Registra los callbacks de la pestaña de predicción.

    Los ganadores y las predicciones se cargan por sesión dentro de cada
    callback (no se cierran sobre DataFrames globales).
    """

    @app.callback(
        Output("prediccion-abx", "options"),
        Output("prediccion-abx", "value"),
        Input("prediccion-especie", "value"),
        Input("prediccion-store", "data"),
    )
    def actualizar_antibioticos(especie, _version):
        _, ganadores = cargar_resultados(obtener_session_id())
        if especie is None or ganadores is None or ganadores.empty:
            return [], None

        antibioticos = sorted(
            ganadores.loc[ganadores["especie"] == especie, "antibiotico"]
            .dropna()
            .unique()
        )
        opciones = [{"label": a, "value": a} for a in antibioticos]
        valor = antibioticos[0] if antibioticos else None
        return opciones, valor

    @app.callback(
        Output("grafico-prediccion", "figure"),
        Input("prediccion-especie", "value"),
        Input("prediccion-abx", "value"),
        Input("prediccion-store", "data"),
    )
    def actualizar_grafico(especie, antibiotico, _version):
        df_predicciones, ganadores = cargar_resultados(obtener_session_id())
        if (
            especie is None
            or antibiotico is None
            or df_predicciones is None
            or df_predicciones.empty
        ):
            fig = go.Figure()
            fig.update_layout(
                title="Seleccione una especie y un antibiótico",
                height=500,
            )
            return fig

        modelo = None
        if ganadores is not None and not ganadores.empty:
            fila = ganadores[
                (ganadores["especie"] == especie)
                &
                (ganadores["antibiotico"] == antibiotico)
            ]
            if not fila.empty:
                modelo = fila.iloc[0]["modelo"]

        return figura_prediccion(
            df_predicciones,
            especie,
            antibiotico,
            modelo=modelo,
        )

    @app.callback(
        Output("estado-generacion", "children"),
        Output("estado-generacion", "style"),
        Output("estado-generacion", "className"),
        Output("btn-generar-prediccion", "disabled"),
        Output("prediccion-interval", "disabled"),
        Input("btn-generar-prediccion", "n_clicks"),
        prevent_initial_call=True,
    )
    def iniciar(_n_clicks):
        session_id = obtener_session_id()
        iniciado, aviso = iniciar_generacion(session_id)
        estado = leer_estado(session_id)

        if estado["estado"] == "running":
            texto, clase = presentacion(estado)
            return texto, {"display": "block"}, clase, True, False

        return aviso, {"display": "block"}, "alert alert-warning", False, True

    @app.callback(
        Output("prediccion-store", "data"),
        Output("estado-generacion", "children", allow_duplicate=True),
        Output("estado-generacion", "style", allow_duplicate=True),
        Output("estado-generacion", "className", allow_duplicate=True),
        Output("btn-generar-prediccion", "disabled", allow_duplicate=True),
        Output("prediccion-interval", "disabled", allow_duplicate=True),
        Input("prediccion-interval", "n_intervals"),
        prevent_initial_call=True,
    )
    def consultar_estado(_n_intervals):
        estado = leer_estado(obtener_session_id())
        texto, clase = presentacion(estado)
        en_curso = estado["estado"] == "running"
        visible = {"display": "none"} if estado["estado"] == "idle" else {"display": "block"}

        # Al terminar, el Timestamp del estado dispara el refresco de los
        # dropdowns y del gráfico con los resultados recién generados.
        version = estado.get("ts") if estado["estado"] == "done" else dash.no_update

        return version, texto, visible, clase, en_curso, not en_curso

    # Aviso del navegador al cerrar/recargar mientras hay una generación en
    # curso (assets/beforeunload.js lee esta variable global).
    app.clientside_callback(
        """
        function(deshabilitado) {
            window.__prediccionEnCurso = !!deshabilitado;
            return !!deshabilitado;
        }
        """,
        Output("prediccion-activa", "data"),
        Input("btn-generar-prediccion", "disabled"),
    )
