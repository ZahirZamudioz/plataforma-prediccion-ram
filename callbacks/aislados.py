"""Callbacks de la pestaña Aislados (gráfico de resistencia en el tiempo)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output

from config import COLORES_ESPECIES, ESPECIES_FIJAS
from datos.gestor_datos import cargar_datos
from datos.transformaciones import calcular_conteos_porcentajes
from sesion import obtener_session_id


def registrar(app, generar_orden_meses, figura_vacia):

    @app.callback(
        Output("grafico_resistencia", "figure"),
        Input("abx_unico", "value"),
        Input("year-selector", "value")
    )
    def actualizar_grafico(abx_1, selected_year):
        if not abx_1:
            return go.Figure()

        df = cargar_datos(selected_year, obtener_session_id()) if selected_year else None
        if df is None or df.empty:
            return figura_vacia()

        count_table = calcular_conteos_porcentajes(df)
        df_grafLineas = count_table[count_table['total'] >= 10].copy()
        df_grafLineas["fecha"] = pd.Categorical(
            df_grafLineas["fecha"], categories=generar_orden_meses(selected_year), ordered=True
        )

        df_1 = df_grafLineas[(df_grafLineas["antibiotico"] == abx_1) & (df_grafLineas["especie"].isin(ESPECIES_FIJAS))]
        df_1_grouped = df_1.groupby(["fecha", "especie"], as_index=False)["R (%)"].mean()
        df_1_grouped = df_1_grouped.sort_values("fecha")

        fig = px.line(
            df_1_grouped,
            x="fecha",
            y="R (%)",
            color="especie",
            markers=True,
            title=f"Resistencia a {abx_1} según especie bacteriana",
            labels={"fecha": "Mes", "R (%)": "Porcentaje de resistencia (%)", "especie": "Especie bacteriana"},
            color_discrete_map=COLORES_ESPECIES,
            category_orders={"fecha": generar_orden_meses(selected_year)}
        )
        fig.update_layout(hovermode="x unified")
        return fig
