"""Callbacks de la pestaña Cargar Datos y del modal de reporte."""
import base64
import json

from dash import Input, Output, State, dcc, dash, html, ALL, ctx

from datos.gestor_datos import (
    procesar_archivo_subido,
    obtener_anios_disponibles,
    obtener_anios_con_reporte,
    eliminar_datos,
    eliminar_todos_datos,
)
from reportes.reportes import (
    generar_html_reporte,
    generar_excel_reporte,
    guardar_reporte,
    cargar_reporte,
)
from layout.reporte import crear_lista_datos
from sesion import obtener_session_id


def registrar(app, invalidar_visualizaciones):

    # 1B: feedback inmediato al pulsar "Procesar datos". Corre en el navegador,
    # así que se muestra aunque el worker tarde en responder. El callback de
    # servidor restaura ambos componentes al terminar (éxito o error).
    app.clientside_callback(
        """
        function(n_clicks) {
            if (!n_clicks) {
                return [
                    window.dash_clientside.no_update,
                    window.dash_clientside.no_update
                ];
            }
            return [{"display": "block"}, true];
        }
        """,
        Output("processing-indicator", "style", allow_duplicate=True),
        Output("btn-process", "disabled", allow_duplicate=True),
        Input("btn-process", "n_clicks"),
        prevent_initial_call=True,
    )

    @app.callback(
        [Output("upload-status", "children"),
         Output("upload-status", "style"),
         Output("upload-status", "className")],
        Input("upload-data", "contents"),
        Input("upload-data", "filename"),
        Input("input-year", "value"),
        prevent_initial_call=True
    )
    def update_upload_status(contents, filename, year):
        if contents and filename:
            return f"📄 Archivo '{filename}' cargado. Listo para procesar para el año {year}.", {"display": "block"}, "alert alert-info"
        return "⚠️ Seleccione un archivo y un año", {"display": "block"}, "alert alert-warning"

    # Procesar archivo subido
    @app.callback(
        [Output("upload-status", "children", allow_duplicate=True),
         Output("upload-status", "style", allow_duplicate=True),
         Output("upload-status", "className", allow_duplicate=True),
         Output("year-selector", "options"),
         Output("year-selector", "value"),
         Output("processing-report-content", "children", allow_duplicate=True),
         Output("processing-report-modal", "is_open", allow_duplicate=True),
         Output("reporte-objetivo", "data", allow_duplicate=True),
         Output("processing-indicator", "style"),
         Output("btn-process", "disabled")],
        Input("btn-process", "n_clicks"),
        [State("upload-data", "contents"),
         State("upload-data", "filename"),
         State("input-year", "value")],
        prevent_initial_call=True
    )
    def procesar_archivo(n_clicks, contents, filename, year):
        session_id = obtener_session_id()
        if n_clicks is None or not contents or not year:
            return ("Seleccione archivo y año",
                    {"display": "block"}, "alert alert-warning",
                    [{"label": str(y), "value": y} for y in obtener_anios_disponibles(session_id)],
                    dash.no_update,  # no cambiar value
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    {"display": "none"},
                    False)

        try:
            decoded_content = base64.b64decode(contents.split(',')[1])
            df_procesado, reporte = procesar_archivo_subido(decoded_content, year, session_id)
            # Actualizar opciones del dropdown con los años disponibles
            anios = obtener_anios_disponibles(session_id)

            reporte_html = generar_html_reporte(reporte, filename, year)

            # Persistir el reporte en disco (sobrevive a reinicios y workers)
            guardar_reporte(reporte, filename, year, session_id)

            # El año pudo re-procesarse con datos nuevos: invalidar el cache de visualizaciones
            invalidar_visualizaciones(year, session_id)

            return (f"✅ '{filename}' procesado para {year}! ({len(df_procesado)} registros). "
                    "Genera las predicciones en la pestaña 'Predicción'.",
                    {"display": "block"},
                    "alert alert-success",
                    [{"label": str(y), "value": y} for y in anios], year, reporte_html, True,
                    year,  # el reporte mostrado corresponde a este año
                    {"display": "none"},
                    False)
        except Exception as e:
            anios = obtener_anios_disponibles(session_id)
            return (
                f"❌ Error al procesar el archivo: {str(e)}",
                {"display": "block"},
                "alert alert-danger",
                [{"label": str(y), "value": y} for y in anios],
                dash.no_update,  # no cambiar el año seleccionado
                html.Div([
                    html.Strong("Error en el procesamiento:"),
                    html.Br(),
                    str(e)
                ], className="alert alert-danger m-3"),
                False,  # no abrir el modal de reporte
                dash.no_update,
                {"display": "none"},
                False,
            )

    # Ver el reporte de un año concreto (desde disco)
    @app.callback(
        [Output("processing-report-content", "children", allow_duplicate=True),
         Output("processing-report-modal", "is_open", allow_duplicate=True),
         Output("reporte-objetivo", "data", allow_duplicate=True)],
        Input({"type": "ver-reporte", "index": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def ver_reporte(n_clicks_list):
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update
        cambio = ctx.triggered[0]
        if not cambio.get("value"):
            return dash.no_update, dash.no_update, dash.no_update
        anio = json.loads(cambio["prop_id"].rsplit(".", 1)[0])["index"]

        datos = cargar_reporte(anio, obtener_session_id())
        if datos is not None:
            return (
                generar_html_reporte(
                    datos["reporte"], datos["nombre_archivo"], datos["anio"]
                ),
                True,
                anio,
            )
        return (
            html.Div([
                html.Strong(f"No hay reporte guardado para el año {anio}. "),
                "Sube los datos de ese año en la pestaña 'Cargar Datos' "
                "para generarlo.",
            ], className="alert alert-warning m-3"),
            True,
            dash.no_update,
        )

    @app.callback(
        Output("download-reporte-excel", "data"),
        Input("btn-descargar-reporte", "n_clicks"),
        State("reporte-objetivo", "data"),
        prevent_initial_call=True
    )
    def descargar_reporte_excel(n_clicks, year):
        datos = cargar_reporte(year, obtener_session_id())
        if not datos:
            return dash.no_update

        return dcc.send_bytes(
            generar_excel_reporte(datos["reporte"]),
            filename=f"reporte_procesamiento_{datos['anio']}.xlsx"
        )

    @app.callback(
        Output("processing-report-modal", "is_open", allow_duplicate=True),
        Input("close-report-modal", "n_clicks"),
        State("processing-report-modal", "is_open"),
        prevent_initial_call=True
    )
    def cerrar_modal(n_clicks, is_open):
        if n_clicks:
            return False
        return is_open

    # --- Gestión de datos: listado y borrado por año ---

    @app.callback(
        Output("lista-datos-cargados", "children"),
        Input("year-selector", "options"),
        Input("processing-report-content", "children"),
    )
    def render_lista_datos(_options, _reporte):
        # Se re-renderiza cuando cambian los años (carga/borrado) o cuando
        # aparece un nuevo reporte tras procesar un archivo.
        return crear_lista_datos(obtener_session_id())

    @app.callback(
        [Output("modal-confirmar-eliminar", "is_open"),
         Output("texto-eliminar", "children"),
         Output("eliminar-objetivo", "data")],
        Input({"type": "accion-eliminar", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def abrir_confirmacion_eliminacion(_clicks):
        # Con Input de patrón (ALL), este callback se dispara también cuando la
        # lista de botones se re-renderiza (n_clicks=None). Solo abrimos el modal
        # si de verdad hubo un clic (valor de n_clicks verdadero).
        objetivo = None
        for cambio in ctx.triggered:
            if cambio.get("value"):
                prop_id = cambio["prop_id"].rsplit(".", 1)[0]
                try:
                    objetivo = json.loads(prop_id)["index"]
                except (ValueError, KeyError, TypeError):
                    objetivo = None
                break

        if objetivo is None:
            return dash.no_update, dash.no_update, dash.no_update

        if objetivo == "todos":
            texto = ("¿Seguro que deseas eliminar TODOS los datos cargados? "
                     "Esta acción no se puede deshacer.")
        else:
            texto = (f"¿Seguro que deseas eliminar los datos del año {objetivo}? "
                     "Esta acción no se puede deshacer.")
        return True, texto, objetivo

    @app.callback(
        [Output("year-selector", "options", allow_duplicate=True),
         Output("year-selector", "value", allow_duplicate=True),
         Output("modal-confirmar-eliminar", "is_open", allow_duplicate=True)],
        Input("btn-confirmar-eliminar", "n_clicks"),
        [State("eliminar-objetivo", "data"),
         State("year-selector", "value")],
        prevent_initial_call=True,
    )
    def confirmar_eliminacion(n_clicks, objetivo, valor_actual):
        if not n_clicks or objetivo is None:
            return dash.no_update, dash.no_update, dash.no_update

        session_id = obtener_session_id()

        if objetivo == "todos":
            eliminados = eliminar_todos_datos(session_id)
        else:
            anio = int(objetivo)
            eliminar_datos(anio, session_id)
            eliminados = [anio]

        for anio in eliminados:
            invalidar_visualizaciones(anio, session_id)

        anios = obtener_anios_disponibles(session_id)
        opciones = [{"label": str(y), "value": y} for y in anios]
        if valor_actual in anios:
            nuevo_valor = valor_actual
        else:
            nuevo_valor = max(anios) if anios else None

        return opciones, nuevo_valor, False

    @app.callback(
        Output("modal-confirmar-eliminar", "is_open", allow_duplicate=True),
        Input("btn-cancelar-eliminar", "n_clicks"),
        prevent_initial_call=True,
    )
    def cancelar_eliminacion(n_clicks):
        return False
