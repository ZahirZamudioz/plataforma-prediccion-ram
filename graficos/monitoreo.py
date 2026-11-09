import numpy as np
import plotly.express as px
from dash import dash_table


def crear_fig_aislados(conteo_especies, orden_especies):
    category_colors = {
        "Gram negativa": "#A5005A",
        "Gram positiva": "#F48FB1",
        "Hongo": "#81C784",
    }

    fig = px.bar(
        conteo_especies,
        x="especie",
        y="aislados",
        color="Grupo_principal" if "Grupo_principal" in conteo_especies.columns else None,
        color_discrete_map=category_colors if "Grupo_principal" in conteo_especies.columns else None,
        labels={"aislados": "Número de aislamientos", "especie": "Especie bacteriana"},
        title="Número de aislamientos por especie bacteriana" 
    )

    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        legend_title=None
    )

    fig.update_xaxes(categoryorder="array", categoryarray=orden_especies)
    fig.update_yaxes(
        type="log",
        tickvals=[1, 10, 100, 1000, 10000],
        ticktext=["1", "10", "100", "1000", "10k"]
    )
    return fig


def crear_heatmap_resistencia(pivot_R, pivot_S, pivot_I, pivot_Inconcluyente,
                              pivot_R_count, pivot_S_count, pivot_I_count, pivot_Inconcluyente_count,
                              yaxis_title):
    customdata = np.stack([
        pivot_S.values, pivot_I.values, pivot_Inconcluyente.values,
        pivot_R_count.values, pivot_S_count.values, pivot_I_count.values, pivot_Inconcluyente_count.values
    ], axis=-1)

    fig = px.imshow(
        pivot_R,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Reds",
        labels={"color": "Resistencia (%)"}
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title=yaxis_title,
        xaxis_title="Antibiótico",
        height=600,
        coloraxis_colorbar={"title": "R (%)"},
        xaxis_side="top"
    )
    fig.update_traces(
        customdata=customdata,
        hovertemplate="Especie: %{y}<br>Antibiótico: %{x}<br>R (%): %{z:.1f}; n = %{customdata[3]:.0f}<br>S (%): %{customdata[0]:.1f}; n = %{customdata[4]:.0f}<br>I (%): %{customdata[1]:.1f}; n = %{customdata[5]:.0f}<br>Inconcluyente (%): %{customdata[2]:.1f}; n = %{customdata[6]:.0f}",
        textfont_size=14
    )
    return fig


def crear_fig_localizacion(conteo_servicio):
    fig = px.bar(
        conteo_servicio,
        x="Tipo de localizacion",
        y="Porcentaje",
        labels={"Porcentaje": "Porcentaje (%)", "Tipo de localización": "Tipo de Localizacion"},
        title="Pocentajes de muestra según servicio",
        color_discrete_sequence=["#636EFA"]
    )
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        showlegend=False
    )
    return fig


def crear_fig_muestra(conteo_muestra):
    fig = px.bar(
        conteo_muestra,
        x="Tipo de muestra",
        y="Porcentaje",
        labels={"Porcentaje": "Porcentaje de muestras (%)", "Tipo de muestra": "Tipo de muestra"},
        title="Distribución porcentual de las muestras según tipo",
        color_discrete_sequence=["#EF553B"],
    )
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        showlegend=False
    )
    return fig


def crear_fig_edad(conteo_edad):
    fig = px.bar(
        conteo_edad,
        x="Rango_edad",
        y="n",
        labels={"n": "Conteo", "Rango_edad": "Rango de Edad"},
        title="Número de muestras según edad",
        color_discrete_sequence=["#00CC96"]
    )
    fig.update_layout(
        height=400,
        xaxis_tickangle=-45,
        showlegend=False
    )
    return fig


def crear_fig_servicio_muestras(conteo_servicio_muestras, orden_servicios, orden_tipos_muestra):
    fig = px.bar(
        conteo_servicio_muestras,
        x="Tipo de localizacion",
        y="Conteo",
        color="Tipo de muestra",
        title="Distribución del tipo de muestras analizadas según servicio",
        labels={"Conteo": "Conteo", "Tipo de localizacion": "Servicio", "Tipo de muestra": "Tipo de Muestra"},
        category_orders={
            "Tipo de localizacion": orden_servicios,
            "Tipo de muestra": orden_tipos_muestra
        },
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig.update_traces(
        marker_line_width=1,
        marker_line_color='black'
    )
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        showlegend=True,
        legend_title="Tipo de Muestra"
    )
    return fig


def crear_fig_muestra_especies(conteo_muestra_especies, orden_muestras, orden_de_especies):
    fig = px.bar(
        conteo_muestra_especies,
        x="Tipo de muestra",
        y="Conteo",
        color="especie",
        title="Aislamientos bacterianos según su origen de la muestra",
        labels={"Conteo": "Conteo", "Tipo de muestra": "Tipo de Muestra", "perfil_especies": "Perfil de Especies"},
        category_orders={
            "Tipo de muestra": orden_muestras,
            "especie": orden_de_especies
        },
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig.update_traces(
        marker_line_width=1,
        marker_line_color='black'
    )
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        showlegend=True,
        legend_title="Especies"
    )
    return fig


def construir_tabla(tabla_id, columnas, records, fixed_rows=None):
    kwargs = {
        "id": tabla_id,
        "columns": columnas,
        "data": records,
        "style_table": {
            "overflowX": "auto",
            "overflowY": "auto",
            "height": "600px",
        },
        "style_cell": {
            "textAlign": "left",
            "padding": "5px",
            "fontSize": "14px"
        },
        "style_header": {
            "backgroundColor": "#f8f9fa",
            "fontWeight": "bold"
        },
    }
    if fixed_rows is not None:
        kwargs["fixed_rows"] = fixed_rows
    return dash_table.DataTable(**kwargs)


def construir_tabla_localizacion(conteo_servicio_tabla):
    return construir_tabla(
        "tabla_localizacion",
        [
            {"name": "Servicio", "id": "Tipo de localizacion"},
            {"name": "n", "id": "n"},
            {"name": "Porcentaje (%)", "id": "Porcentaje"}
        ],
        conteo_servicio_tabla.to_dict("records"),
    )


def construir_tabla_muestra(conteo_muestra_tabla):
    return construir_tabla(
        "tabla_muestra",
        [
            {"name": "Tipo de Muestra", "id": "Tipo de muestra"},
            {"name": "n", "id": "n"},
            {"name": "Porcentaje (%)", "id": "Porcentaje"}
        ],
        conteo_muestra_tabla.to_dict("records"),
        fixed_rows={"headers": True},
    )


def construir_tabla_servicio_muestras(conteo_servicio_muestras):
    return construir_tabla(
        "tabla_servicio_muestras",
        [
            {"name": "Servicio", "id": "Tipo de localizacion"},
            {"name": "Tipo de Muestra", "id": "Tipo de muestra"},
            {"name": "Conteo", "id": "Conteo"},
            {"name": "Porcentaje (%)", "id": "Porcentaje"}
        ],
        conteo_servicio_muestras.to_dict("records"),
    )


def construir_tabla_muestra_especies(conteo_muestra_especies):
    return construir_tabla(
        "tabla_muestra_especies",
        [
            {"name": "Tipo de Muestra", "id": "Tipo de muestra"},
            {"name": "Especies", "id": "especie"},
            {"name": "Conteo", "id": "Conteo"},
            {"name": "Porcentaje (%)", "id": "Porcentaje"}
        ],
        conteo_muestra_especies.to_dict("records"),
    )
