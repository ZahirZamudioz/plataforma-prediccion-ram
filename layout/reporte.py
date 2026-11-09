import dash_bootstrap_components as dbc
from dash import dcc, html
from datos.gestor_datos import obtener_anios_disponibles, obtener_anios_con_reporte


# Componente de carga de nuevos datos (contenido de la pestaña "Cargar Datos")
upload_section = html.Div([
    html.H3("Cargar nuevos datos", className="mb-3"),
    # Requisitos del archivo a cargar
    html.P("El archivo debe contener, como mínimo, las siguientes columnas:", className="mb-1"),
    html.Ul([
        html.Li([html.Strong("fecha"), " → fecha de toma o recolección de la muestra."]),
        html.Li([html.Strong("Tipo de localizacion"), " → tipo de servicio hospitalario."]),
        html.Li([html.Strong("Edad"), " → edad del paciente."]),
        html.Li([html.Strong("SPEC_NUM"), " → identificador de la muestra."]),
        html.Li([html.Strong("Tipo de muestra"), " → Tipo de muestra obtenida."]),
        html.Li([html.Strong("especie"), " → especie bacteriana."]),
    ], className="mb-2"),
    html.P("El formato admitido es Excel (.xlsx). Ingrese el año al que corresponden "
           "los datos antes de seleccionar el archivo.", className="mb-3"),
    dbc.Row([
        dbc.Col([
            dcc.Input(
                id="input-year",
                type="number",
                placeholder="Ingrese el año (ej. 2023)",
                min=2000,
                max=2030,
                value=2023,
                className="form-control"
            )
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    html.I(className="fas fa-file-excel me-2"),
                    "Seleccionar archivo Excel"
                ], className="btn btn-outline-primary w-100"),
                multiple=False
            )
        ], width=6),
        dbc.Col([
            dbc.Button([html.I(className="fas fa-gears me-2"), "Procesar datos"],
                       id="btn-process", color="primary", className="w-100")
        ], width=6)
    ], className="mt-2 mb-2"),
    html.Div(
        html.Span([
            html.I(className="fas fa-spinner fa-spin me-2"),
            "Procesando el archivo… esto puede tardar unos segundos.",
        ]),
        id="processing-indicator",
        className="alert alert-info mt-2",
        style={"display": "none"},
    ),
    html.Div(id="upload-status", className="alert alert-info mt-2", style={"display": "none"})
], className="card p-3 mb-4")


# Modal de reporte de procesamiento
modal_reporte = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Reporte de Procesamiento")),
        dbc.ModalBody(html.Div(id="processing-report-content")),
        dbc.ModalFooter(
            [
                dbc.Button(
                    "Descargar reporte completo",
                    id="btn-descargar-reporte",
                    color="success",   # Verde tipo Excel
                    className="me-auto"
                ),
                dbc.Button(
                    "Cerrar",
                    id="close-report-modal",
                    className="ms-auto"
                )
            ]
        ),
    ],
    id="processing-report-modal",
    is_open=False,
    size="xl",
    scrollable=True,
    centered=True,
)


download_reporte = dcc.Download(id="download-reporte-excel")


def crear_lista_datos(session_id):
    """Lista única de años: permite ver el reporte de cada uno y eliminar sus datos."""
    anios = obtener_anios_disponibles(session_id)
    anios_con_reporte = set(obtener_anios_con_reporte(session_id))

    if not anios:
        return html.Div("No hay datos cargados.", className="text-muted")

    filas = []
    for anio in anios:
        tiene_reporte = anio in anios_con_reporte
        filas.append(
            dbc.ListGroupItem([
                dbc.Row([
                    dbc.Col(
                        html.Span([html.I(className="fas fa-calendar-days me-2"),
                                   str(anio)]),
                        width="auto"
                    ),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-file-lines me-2"), "Ver reporte"],
                            id={"type": "ver-reporte", "index": anio},
                            color="info", outline=True, size="sm",
                            disabled=not tiene_reporte,
                            title=(f"Ver reporte de {anio}" if tiene_reporte
                                   else "No hay reporte para este año"),
                            className="me-2"
                        ),
                        dbc.Button(
                            html.I(className="fas fa-trash-can"),
                            id={"type": "accion-eliminar", "index": anio},
                            color="danger", outline=True, size="sm",
                            title=f"Eliminar datos de {anio}",
                        ),
                    ], width="auto"),
                ], justify="between", align="center", className="g-0")
            ])
        )

    return dbc.ListGroup(filas, flush=True)


# Gestión de datos cargados (contenido de la pestaña "Cargar Datos")
gestion_datos = dbc.Card([
    dbc.CardHeader(
        html.H5([html.I(className="fas fa-database me-2"), "Gestión de datos"],
                className="mb-0")
    ),
    dbc.CardBody([
        html.P("Años cargados en la plataforma:", className="mb-2"),
        html.Div(id="lista-datos-cargados"),
        html.Hr(),
        dbc.Button(
            [html.I(className="fas fa-trash-can me-2"), "Eliminar todos los datos"],
            id={"type": "accion-eliminar", "index": "todos"},
            color="danger", outline=True, className="mt-1"
        ),
    ]),
], className="mb-4")


# Modal de confirmación para eliminar datos
modal_confirmar_eliminacion = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Confirmar eliminación")),
        dbc.ModalBody(html.Div(id="texto-eliminar")),
        dbc.ModalFooter([
            dbc.Button([html.I(className="fas fa-trash-can me-2"), "Eliminar"],
                       id="btn-confirmar-eliminar", color="danger"),
            dbc.Button("Cancelar", id="btn-cancelar-eliminar", color="secondary"),
        ]),
    ],
    id="modal-confirmar-eliminar",
    is_open=False,
    centered=True,
)
