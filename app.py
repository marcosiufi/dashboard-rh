import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# ===== LEITURA DOS EXCEL =====
df_head = pd.read_csv("https://docs.google.com/spreadsheets/d/1E9ja83RZseiOC8iGlgsEZ4wk--KD6dFm0OM1bociUB4/export?format=csv")
df_rs = pd.read_csv("https://docs.google.com/spreadsheets/d/1xlQ1cMTsIjEP-QZAQvOdgkZHGSfvKh7zIn7rTsYnu5o/export?format=csv")

df_head.columns = df_head.columns.str.strip()
df_rs.columns = df_rs.columns.str.strip()

df_head["Início previsto"] = pd.to_datetime(df_head["Início previsto"])
df_rs["Início previsto"] = pd.to_datetime(df_rs["Início previsto"])

df_rs["Etapa"] = df_rs["Etapa"].astype(str).str.strip()

# ===== APP =====
app = Dash(__name__)
server = app.server

# ===== LAYOUT =====
app.layout = html.Div(
    style={
        "backgroundColor": "#F4F6F8",
        "padding": "20px",
        "fontFamily": "Arial"
    },
    children=[

        html.H1("Dashboard de Recrutamento & Headcount", style={"color": "#2E2E2E"}),

        # ===== FILTROS =====
        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "20px"},
            children=[
                dcc.Dropdown(id="empresa", placeholder="Empresa", style={"width": "180px"}),
                dcc.Dropdown(id="departamento", placeholder="Departamento", style={"width": "180px"}),
                dcc.Dropdown(id="area", placeholder="Área", style={"width": "160px"}),
                dcc.Dropdown(id="secao", placeholder="Seção", style={"width": "160px"}),
                dcc.Dropdown(id="cargo", placeholder="Cargo", style={"width": "160px"}),
                dcc.Dropdown(id="funcao", placeholder="Função", style={"width": "160px"})
            ]
        ),

        # ===== KPI =====
        html.Div(
            style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
            children=[

                html.Div(
                    id="total-ativos",
                    style={
                        "background": "white",
                        "padding": "22px",
                        "borderRadius": "14px",
                        "boxShadow": "0 3px 8px rgba(0,0,0,0.08)",
                        "fontSize": "28px",
                        "color": "#5B7DB1",
                        "flex": "1"
                    }
                ),

                html.Div(
                    "Metas por cargo",
                    style={
                        "background": "white",
                        "padding": "22px",
                        "borderRadius": "14px",
                        "boxShadow": "0 3px 8px rgba(0,0,0,0.08)",
                        "flex": "1"
                    }
                ),

                html.Div(
                    "Performance mensal",
                    style={
                        "background": "white",
                        "padding": "22px",
                        "borderRadius": "14px",
                        "boxShadow": "0 3px 8px rgba(0,0,0,0.08)",
                        "flex": "1"
                    }
                )
            ]
        ),

        # ===== GRÁFICOS =====
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "20px"},
            children=[

                html.Div(
                    dcc.Graph(id="grafico-metas"),
                    style={
                        "background": "white",
                        "padding": "18px",
                        "borderRadius": "14px",
                        "boxShadow": "0 3px 8px rgba(0,0,0,0.08)"
                    }
                ),

                html.Div(
                    dcc.Graph(id="funil-rs"),
                    style={
                        "background": "white",
                        "padding": "18px",
                        "borderRadius": "14px",
                        "boxShadow": "0 3px 8px rgba(0,0,0,0.08)"
                    }
                )
            ]
        )
    ]
)

# ===== POPULA EMPRESA =====
@app.callback(
    Output("empresa", "options"),
    Input("empresa", "id")
)
def carregar_empresas(_):
    return [{"label": e, "value": e} for e in df_head["Empresa"].dropna().unique()]


# ===== CALLBACK PRINCIPAL =====
@app.callback(
    Output("departamento", "options"),
    Output("area", "options"),
    Output("secao", "options"),
    Output("cargo", "options"),
    Output("funcao", "options"),
    Output("total-ativos", "children"),
    Output("grafico-metas", "figure"),
    Output("funil-rs", "figure"),
    Input("empresa", "value"),
    Input("departamento", "value"),
    Input("area", "value"),
    Input("secao", "value"),
    Input("cargo", "value"),
    Input("funcao", "value")
)
def atualizar(empresa, departamento, area, secao, cargo, funcao):

    # ===== HEADCOUNT =====
    df = df_head.copy()

    if empresa:
        df = df[df["Empresa"] == empresa]
    if departamento:
        df = df[df["Departamento"] == departamento]
    if area:
        df = df[df["Área"] == area]
    if secao:
        df = df[df["Seção"] == secao]
    if cargo:
        df = df[df["Cargo"] == cargo]
    if funcao:
        df = df[df["Função"] == funcao]

    departamentos = [{"label": d, "value": d} for d in df["Departamento"].dropna().unique()]
    areas = [{"label": a, "value": a} for a in df["Área"].dropna().unique()]
    secoes = [{"label": s, "value": s} for s in df["Seção"].dropna().unique()]
    cargos = [{"label": c, "value": c} for c in df["Cargo"].dropna().unique()]
    funcoes = [{"label": f, "value": f} for f in df["Função"].dropna().unique()]

    total = int(df["Contratado"].sum())

    # ===== METAS =====
    metas = df.copy()
    metas["Mes"] = metas["Início previsto"].dt.to_period("M").astype(str)
    metas = metas.groupby("Mes")[["Previsto", "Contratado"]].sum().reset_index()

    fig_metas = px.bar(
        metas,
        x="Mes",
        y=["Previsto", "Contratado"],
        barmode="group",
        text_auto=True,
        color_discrete_sequence=["#B0B7C3", "#5B7DB1"]
    )

    fig_metas.update_layout(
        title="Previsto x Contratado por mês",
        plot_bgcolor="white",
        paper_bgcolor="white",
        bargap=0.25
    )

    # ===== FUNIL COM ETAPAS NUMERADAS =====
    rs = df_rs.copy()

    if empresa:
        rs = rs[rs["Empresa"] == empresa]
    if departamento:
        rs = rs[rs["Departamento"] == departamento]
    if area:
        rs = rs[rs["Área"] == area]
    if secao:
        rs = rs[rs["Seção"] == secao]
    if cargo:
        rs = rs[rs["Cargo"] == cargo]
    if funcao:
        rs = rs[rs["Função"] == funcao]

    etapas = [
        "1. Não iniciado",
        "2. Divulgação",
        "3. Triagem",
        "4. Entrevistas",
        "5. Testes e avaliações",
        "6. Proposta",
        "7. Contratados",
        "8. Reprovados"
    ]

    dados_funil = []

    for etapa in etapas:

        if etapa in ["1. Não iniciado", "2. Divulgação", "3. Triagem"]:
            valor = rs.loc[rs["Etapa"] == etapa, "Total de posições"].sum()
        else:
            valor = rs.loc[rs["Etapa"] == etapa, "Nome do candidato"].notna().sum()

        dados_funil.append({
            "Etapa": etapa,
            "Quantidade": int(valor)
        })

    funil = pd.DataFrame(dados_funil)

    fig_funil = px.funnel(
        funil,
        x="Quantidade",
        y="Etapa",
        color_discrete_sequence=["#5B7DB1"]
    )

    fig_funil.update_layout(
        title="Funil de Recrutamento",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    return (
        departamentos,
        areas,
        secoes,
        cargos,
        funcoes,
        f"Total de ativos: {total}",
        fig_metas,
        fig_funil
    )

# ===== RUN =====
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)