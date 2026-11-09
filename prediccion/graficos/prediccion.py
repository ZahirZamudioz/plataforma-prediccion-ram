"""Gráficos para la pestaña de predicción."""
import pandas as pd
import plotly.graph_objects as go


def figura_prediccion(df_predicciones, especie, antibiotico, modelo=None):
    """
    Serie observada + predicción futura (línea roja punteada) para una
    combinación especie-antibiótico, replicando el estilo original del
    proyecto de predicción.
    """
    df = df_predicciones[
        (df_predicciones["especie"] == especie)
        &
        (df_predicciones["antibiotico"] == antibiotico)
    ].copy()

    if df.empty:
        return go.Figure()

    df["trimestre"] = df["trimestre"].astype(str)

    df_hist = df[df["tipo"] == "observado"].copy()
    df_pred = df[df["tipo"] == "prediccion"].copy()

    if not df_hist.empty and not df_pred.empty:
        ultimo_observado = df_hist.iloc[-1][["trimestre", "valor"]].to_dict()
        bridge = pd.DataFrame([ultimo_observado])
        df_pred = pd.concat([bridge, df_pred], ignore_index=True)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_hist["trimestre"],
        y=df_hist["valor"],
        mode="lines+markers",
        name="Observado",
        line={"color": "#2c3e50", "width": 2},
        marker={"size": 6},
    ))

    fig.add_trace(go.Scatter(
        x=df_pred["trimestre"],
        y=df_pred["valor"],
        mode="lines+markers",
        name="Predicción",
        line={"color": "#e74c3c", "width": 2, "dash": "dash"},
        marker={"size": 8, "symbol": "diamond"},
    ))

    titulo = f"Predicción {especie} - {antibiotico}"
    if modelo:
        titulo = f"{titulo} (Modelo: {modelo})"

    fig.update_layout(
        title=titulo,
        xaxis_title="Trimestre",
        yaxis_title="Proporción de Resistencia",
        height=500,
        margin={"l": 50, "r": 30, "t": 80, "b": 80},
        xaxis_tickangle=-45,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    return fig
