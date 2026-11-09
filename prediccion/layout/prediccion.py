"""Layout de la pestaña de predicción."""
import dash_bootstrap_components as dbc
from dash import dcc, html

from prediccion.generacion import leer_estado, presentacion
from sesion import obtener_session_id


def _especies(ganadores):
    if ganadores is None or ganadores.empty:
        return []
    return sorted(ganadores["especie"].dropna().unique())


def _antibioticos(ganadores, especie):
    if ganadores is None or ganadores.empty or especie is None:
        return []
    return sorted(
        ganadores.loc[ganadores["especie"] == especie, "antibiotico"]
        .dropna()
        .unique()
    )


def layout_prediccion(ganadores=None):
    especies = _especies(ganadores)
    especie_inicial = especies[0] if especies else None
    antibioticos = _antibioticos(ganadores, especie_inicial)
    antibiotico_inicial = antibioticos[0] if antibioticos else None

    estado = leer_estado(obtener_session_id())
    texto_estado, clase_estado = presentacion(estado)
    en_curso = estado["estado"] == "running"
    visible_estado = (
        {"display": "none"} if estado["estado"] == "idle" else {"display": "block"}
    )

    return dbc.Container([
        html.Div([
            html.H3("Predicción de RAM", className="mb-3"),
            html.P(
                "La predicción de la resistencia antimicrobiana se genera "
                "trimestralmente a partir del último año con datos. Se requiere "
                "un mínimo de 5 años (15 trimestres) consecutivos de datos "
                "válidos. El entrenamiento puede tardar varios minutos; puedes "
                "seguir usando la plataforma, pero no cierres esta pestaña "
                "mientras esté en curso.",
                className="text-muted",
            ),
            dbc.Button(
                [html.I(className="fas fa-gears me-2"), "Generar predicciones"],
                id="btn-generar-prediccion",
                color="primary",
                disabled=en_curso,
            ),
            html.Div(
                html.Div(
                    id="estado-generacion",
                    children=texto_estado,
                    className=clase_estado,
                    style=visible_estado,
                ),
                className="mt-2",
            ),
        ], className="card p-3 mb-4"),
        dcc.Store(id="prediccion-store", data=None),
        dcc.Store(id="prediccion-activa", data=None),
        dcc.Interval(
            id="prediccion-interval", interval=4000, disabled=not en_curso
        ),

        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Label("Especie:", className="me-2"),
                    dcc.Dropdown(
                        id="prediccion-especie",
                        options=[{"label": e, "value": e} for e in especies],
                        value=especie_inicial,
                        clearable=False,
                        style={"minWidth": "260px"},
                    ),
                ], style={"display": "flex", "alignItems": "center"}),
                width=6,
            ),
            dbc.Col(
                html.Div([
                    html.Label("Antibiótico:", className="me-2"),
                    dcc.Dropdown(
                        id="prediccion-abx",
                        options=[{"label": a, "value": a} for a in antibioticos],
                        value=antibiotico_inicial,
                        clearable=False,
                        style={"minWidth": "260px"},
                    ),
                ], style={"display": "flex", "alignItems": "center"}),
                width=6,
            ),
        ], className="mb-3"),

        dcc.Graph(id="grafico-prediccion"),
    ], fluid=True)
