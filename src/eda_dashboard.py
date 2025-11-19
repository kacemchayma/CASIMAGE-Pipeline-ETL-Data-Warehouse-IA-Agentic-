"""
===============================================================================
                     📊 CASIMAGE – Dashboard Clinique & Data Quality
                           Version Professionnelle – GitHub
-------------------------------------------------------------------------------
Objectif :
    Tableau de bord interactif permettant :
        ✔ Analyse clinique (âge, diagnostics, départements…)
        ✔ Analyse qualité des données (missing values, descriptions, etc.)
        ✔ Aperçu dynamique des données
        ✔ Filtrage intelligent par département

Entrée :
    output/casimage_ai_clean.csv (généré par clean_data.py)

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir
===============================================================================
"""

# =============================================================================
# Imports
# =============================================================================

import os
import pandas as pd
from dash import Dash, html, dcc, Input, Output
import plotly.express as px

from config import CLEAN_CSV_PATH


# =============================================================================
# 1️⃣ Chargement du dataset
# =============================================================================
DATA_PATH = CLEAN_CSV_PATH

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        "❌ Fichier 'casimage_ai_clean.csv' introuvable.\n"
        "➡️ Exécute main.py puis clean_data.py avant le dashboard."
    )

df = pd.read_csv(DATA_PATH)
print(f"📂 Dataset chargé ({len(df)} lignes).")


# =============================================================================
# 2️⃣ Sécurisation et nettoyage minimal
# =============================================================================

# ID — Création si manquant
if "ID" not in df.columns:
    df["ID"] = df.index + 1

# Nettoyage textuel du Département
df["Department"] = df["Department"].astype(str).str.strip()
df = df[df["Department"].str.lower() != "non renseigné"]

# ClinicalPresentation sécurisé
df["ClinicalPresentation"] = df.get("ClinicalPresentation", "").astype(str)

# Age (filtrage bornes plausibles)
df["Age"] = pd.to_numeric(df.get("Age"), errors="coerce")
df.loc[(df["Age"] <= 0) | (df["Age"] > 120), "Age"] = None

# Dates → utilisation format explicite pour éviter le warning dayfirst
df["Date"] = pd.to_datetime(df.get("Date"), errors="coerce", format="%Y-%m-%d")
df["Year"] = df["Date"].dt.year

# Tranches d'âge
df["AgeGroup"] = pd.cut(
    df["Age"],
    bins=[0, 20, 40, 60, 80, 150],
    labels=["0–20", "21–40", "41–60", "61–80", "80+"],
    right=False
)

# Qualité description
df["DescriptionLen"] = df["ClinicalPresentation"].astype(str).apply(len)
df["IsBadDescription"] = df["DescriptionLen"] < 15


# =============================================================================
# 3️⃣ Initialisation Dash
# =============================================================================

app = Dash(__name__)
app.title = "📊 CASIMAGE – Dashboard Clinique & Qualité"


# =============================================================================
# 4️⃣ Colonnes affichables (sans NLP_MainPathology)
# =============================================================================

decision_cols = [
    "ID", "Diagnosis", "Department",
    "Sex", "Age", "Year"
]

decision_cols = [c for c in decision_cols if c in df.columns]

default_preview_cols = [
    c for c in ["ID", "Diagnosis", "Department", "Age", "Sex", "Year"]
    if c in decision_cols
]


# =============================================================================
# 5️⃣ Layout Dashboard
# =============================================================================

app.layout = html.Div([

    html.H1("📈 CASIMAGE – Dashboard Clinique & Qualité",
            style={"textAlign": "center"}),

    # -------------------------------------------------------------------------
    # KPI
    # -------------------------------------------------------------------------
    html.Div([
        html.Div([
            html.H4(f"🧮 Total cas : {len(df)}"),
            html.H4(f"🏥 Départements : {df['Department'].nunique()}"),
            html.H4(f"👤 Âge moyen : {round(df['Age'].dropna().mean(), 1)} ans"),
            html.H4(f"🧩 % Desc valides : {100 - round(df['IsBadDescription'].mean()*100, 1)}%"),
            html.H4(f"📉 Missing global : {round(df.isna().mean().mean()*100, 1)}%"),
        ], style={"textAlign": "center"})
    ], style={"display": "flex", "justifyContent": "space-around",
              "marginBottom": "30px"}),

    # -------------------------------------------------------------------------
    # Filtre Département
    # -------------------------------------------------------------------------
    html.H2("🎚 Filtres", style={"textAlign": "center"}),

    html.Div([
        html.Label("🏥 Département :"),
        dcc.Dropdown(
            id="department-filter",
            options=[{"label": d, "value": d}
                     for d in sorted(df["Department"].unique())],
            placeholder="Tous les départements"
        ),
    ], style={"width": "40%", "margin": "auto"}),

    html.Br(), html.Br(),

    # -------------------------------------------------------------------------
    # Section clinique
    # -------------------------------------------------------------------------
    html.H2("🩺 Vue clinique", style={"textAlign": "center"}),

    html.Div([
        html.Div([dcc.Graph(id="diag-chart")], style={"width": "48%"}),
        html.Div([dcc.Graph(id="age-distrib")], style={"width": "48%"})
    ], style={"display": "flex"}),

    html.Br(),

    html.Div([
        html.Div([dcc.Graph(id="age-group")], style={"width": "48%"}),
        html.Div([dcc.Graph(id="cases-year")], style={"width": "48%"})
    ], style={"display": "flex"}),

    html.Br(),

    # -------------------------------------------------------------------------
    # Section Data Quality
    # -------------------------------------------------------------------------
    html.H2("🧹 Data Quality", style={"textAlign": "center"}),

    html.Div([
        html.Div([dcc.Graph(id="missing-values")], style={"width": "48%"}),
        html.Div([dcc.Graph(id="desc-len")], style={"width": "48%"})
    ], style={"display": "flex"}),

    html.Br(),

    # -------------------------------------------------------------------------
    # Section Aperçu Données
    # -------------------------------------------------------------------------
    html.H2("🔍 Aperçu des données", style={"textAlign": "center"}),

    dcc.Dropdown(
        id="column-selector",
        options=[{"label": c, "value": c} for c in decision_cols],
        value=default_preview_cols,
        multi=True,
        style={"width": "70%", "margin": "auto"}
    ),

    html.Div(id="data-preview", style={"margin": "20px"}),

])


# =============================================================================
# 6️⃣ Callback principal
# =============================================================================

@app.callback(
    [
        Output("diag-chart", "figure"),
        Output("age-distrib", "figure"),
        Output("age-group", "figure"),
        Output("cases-year", "figure"),
        Output("missing-values", "figure"),
        Output("desc-len", "figure"),
        Output("data-preview", "children")
    ],
    [
        Input("department-filter", "value"),
        Input("column-selector", "value")
    ]
)
def update_dashboard(selected_dept, selected_cols):

    dff = df.copy()

    # Filtre dynamique
    if selected_dept:
        dff = dff[dff["Department"] == selected_dept]

    # --------------------------- Graphiques cliniques ---------------------------

    diag_counts = dff["Diagnosis"].value_counts().nlargest(10).reset_index()
    diag_counts.columns = ["Diagnosis", "Count"]
    fig_diag = px.bar(diag_counts, x="Diagnosis", y="Count",
                      title="Top 10 diagnostics")

    age_data = dff[dff["Age"].notna()]
    fig_age = px.histogram(age_data, x="Age", nbins=20,
                           title="Distribution des âges")

    age_group_counts = dff["AgeGroup"].value_counts().sort_index().reset_index()
    age_group_counts.columns = ["Tranche d'âge", "Nombre de cas"]
    fig_age_group = px.bar(age_group_counts, x="Tranche d'âge", y="Nombre de cas",
                           title="Répartition par tranche d’âge")

    yearly = dff["Year"].dropna().astype(int).value_counts().sort_index()
    fig_yearly = px.line(x=yearly.index, y=yearly.values, markers=True,
                         title="Cas par année")

    # --------------------------- Data Quality ----------------------------

    missing = dff.isna().sum()
    fig_missing = px.bar(x=missing.index, y=missing.values,
                         title="Valeurs manquantes")
    fig_missing.update_layout(xaxis_tickangle=90)

    fig_desc = px.histogram(dff, x="DescriptionLen", nbins=30,
                            title="Longueur des descriptions cliniques")

    # -------------------------- Aperçu Table ------------------------------

    selected_cols = [c for c in selected_cols if c in dff.columns]
    preview = dff[selected_cols].head(10).to_dict("records")

    table = html.Table([
        html.Thead(html.Tr([html.Th(c) for c in selected_cols])),
        html.Tbody([
            html.Tr([html.Td(row[c]) for c in selected_cols])
            for row in preview
        ])
    ], style={"width": "90%", "margin": "auto",
              "border": "1px solid #ccc"})

    return (fig_diag, fig_age, fig_age_group, fig_yearly,
            fig_missing, fig_desc, table)


# =============================================================================
# 7️⃣ Lancement serveur
# =============================================================================
if __name__ == "__main__":
    print("🚀 Dashboard CASIMAGE → http://127.0.0.1:8050")
    app.run(debug=True)
