import dash_bootstrap_components as dbc
from dash import dcc, html


def layout_muestras(fig_localizacion, tabla_localizacion, fig_muestra, tabla_muestra,
                    fig_edad, fig_servicio_muestras, tabla_servicio_muestras,
                    fig_muestra_especies, tabla_muestra_especies):
    return dbc.Container([
        # 1. Distribución de muestras según servicio
        dbc.Card([
            dbc.CardHeader(html.H5("Distribución de muestras según servicio",
                                   className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        dcc.Graph(id="grafico_localizacion",
                                  figure=fig_localizacion,
                                  style={"height": "600px"}),
                        width=6,
                    ),
                    dbc.Col(tabla_localizacion, width=6),
                ])
            ]),
        ], className="mb-4"),

        # 2. Distribución del tipo de muestras
        dbc.Card([
            dbc.CardHeader(html.H5("Distribución del tipo de muestras",
                                   className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        dcc.Graph(id="grafico_muestra",
                                  figure=fig_muestra,
                                  style={"height": "600px"}),
                        width=6,
                    ),
                    dbc.Col(tabla_muestra, width=6),
                ])
            ]),
        ], className="mb-4"),

        # 3. Distribución de muestras según edad
        dbc.Card([
            dbc.CardHeader(html.H5("Distribución de muestras según edad",
                                   className="mb-0")),
            dbc.CardBody([
                dcc.Graph(id="grafico_edad",
                          figure=fig_edad,
                          style={"height": "400px"}),
            ]),
        ], className="mb-4"),

        # 4. Distribución de tipos de muestra por servicio
        dbc.Card([
            dbc.CardHeader(html.H5("Distribución de tipos de muestra por servicio",
                                   className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        dcc.Graph(id="grafico_servicio_muestras",
                                  figure=fig_servicio_muestras,
                                  style={"height": "600px"}),
                        width=6,
                    ),
                    dbc.Col(tabla_servicio_muestras, width=6),
                ])
            ]),
        ], className="mb-4"),

        # 5. Distribución de especies bacterianas por tipo de muestra
        dbc.Card([
            dbc.CardHeader(html.H5("Distribución de especies bacterianas por tipo de muestra",
                                   className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        dcc.Graph(id="grafico_muestra_especies",
                                  figure=fig_muestra_especies,
                                  style={"height": "600px"}),
                        width=6,
                    ),
                    dbc.Col(tabla_muestra_especies, width=6),
                ])
            ]),
        ], className="mb-4"),
    ], className="mt-3")
