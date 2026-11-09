import dash_bootstrap_components as dbc
from dash import dcc, html


def layout_aislados(fig3, fig_heatmap_pos, fig_heatmap_neg, antibioticos):
    return dbc.Container([
        # Especies bacterianas
        dbc.Card([
            dbc.CardHeader(html.H5("Especies bacterianas", className="mb-0")),
            dbc.CardBody([
                dcc.Graph(id="grafico_aislados", figure=fig3, style={"height": "600px"}),
            ]),
        ], className="mb-4"),

        # Gram Positivas
        dbc.Card([
            dbc.CardHeader(html.H5("Porcentaje de resistencia por especie y antibiótico (Gram Positivas)",
                                   className="mb-0")),
            dbc.CardBody([
                dcc.Graph(id="grafico_heatmap_pos", figure=fig_heatmap_pos, style={"height": "600px"}),
            ]),
        ], className="mb-4"),

        # Gram Negativas
        dbc.Card([
            dbc.CardHeader(html.H5("Porcentaje de resistencia por especie y antibiótico (Gram Negativas)",
                                   className="mb-0")),
            dbc.CardBody([
                dcc.Graph(id="grafico_heatmap_neg", figure=fig_heatmap_neg, style={"height": "1000px"}),
            ]),
        ], className="mb-4"),

        # Resistencia por antibiótico en el tiempo
        dbc.Card([
            dbc.CardHeader(html.H5("Porcentaje de resistencia por antibiótico en el tiempo",
                                   className="mb-0")),
            dbc.CardBody([
                html.Label("Selecciona un antibiótico:"),
                dcc.Dropdown(
                    id="abx_unico",
                    options=[{"label": abx, "value": abx} for abx in antibioticos],
                    value=antibioticos[0] if antibioticos else None,
                    clearable=False,
                ),
                dcc.Graph(id="grafico_resistencia", style={"height": "500px"}),
            ]),
        ], className="mb-4"),
    ], className="mt-3")
