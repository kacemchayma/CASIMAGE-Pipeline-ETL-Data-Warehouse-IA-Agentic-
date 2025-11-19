"""
===============================================================================
                    Analytics & Data Quality – CASIMAGE
===============================================================================

Ce module fournit :
    - Fonctions de nettoyage simple pour valeurs textuelles / numériques / dates
    - Visualisations médicales clés (diagnostics, âge, année, département)
    - Visualisations Data Quality (valeurs manquantes, longueur textes)
    - Analyses avancées (segmentation KMeans sur l'âge)

IMPORTANT :
    ✅ Aucune dépendance à NLP_MainPathology ou colonnes NLP.
    Les analyses se basent uniquement sur les colonnes classiques :
    Diagnosis, Age, Year, Department, Description, Birthdate, Date…

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir
===============================================================================
"""

import re
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import numpy as np  # pour extensions futures


# =============================================================================
# 1️⃣ Nettoyage avancé des champs basiques
# =============================================================================

STOPWORDS_FR = {"de", "du", "des", "la", "le", "et", "à", "au", "une", "un"}

def clean_clinical_text(text: str) -> str:
    """
    Nettoie un texte clinique :
      - suppression balises HTML
      - passage en minuscule
      - retrait de quelques stopwords FR
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<.*?>", " ", text)   # enlever HTML
    text = text.lower()
    text = " ".join([w for w in text.split() if w not in STOPWORDS_FR])
    return text


def clean_numeric(val):
    """
    Convertit une valeur en float ou None si invalide / code manquant.
    """
    if str(val).lower().strip() in {"na", "none", "", "-", "--"}:
        return None
    try:
        return float(val)
    except Exception:
        return None


def clean_date(col: pd.Series) -> pd.Series:
    """
    Nettoyage standard de date :
      - conversion en datetime (dayfirst=True)
      - renvoi de la date (sans l'heure)
    """
    return pd.to_datetime(col, errors="coerce", dayfirst=True).dt.date


def normalize_diagnosis(text: str) -> str:
    """
    Harmonise légèrement la colonne Diagnosis à partir du texte.
    Regroupe quelques familles terminologiques.
    """
    text = clean_clinical_text(text)

    if "algodystroph" in text or "sudeck" in text:
        return "Algodystrophie"

    if "fractur" in text:
        return "Fracture"

    if "necros" in text or "nécros" in text:
        return "Nécrose"

    if "tumeur" in text or "masse" in text:
        return "Tumeur"

    return text.capitalize()


# =============================================================================
# 2️⃣ Visualisations pour décideurs
# =============================================================================

def plot_top_diagnosis(df: pd.DataFrame):
    """
    Affiche le Top 10 des diagnostics.
    """
    if "Diagnosis" not in df.columns:
        print("⚠ 'Diagnosis' non présent dans le DataFrame.")
        return

    plt.figure(figsize=(10, 5))
    df["Diagnosis"].value_counts().head(10).plot(kind="bar", color="royalblue")
    plt.title("Top 10 Pathologies")
    plt.ylabel("Nombre de cas")
    plt.tight_layout()
    plt.show()


def plot_age_distribution(df: pd.DataFrame):
    """
    Distribution de l'âge sur l'ensemble des cas.
    """
    if "Age" not in df.columns:
        print("⚠ 'Age' non présent dans le DataFrame.")
        return

    plt.figure(figsize=(8, 4))
    sns.histplot(df["Age"].dropna(), bins=20, kde=True, color="blue")
    plt.title("Distribution des âges")
    plt.tight_layout()
    plt.show()


def plot_cases_per_year(df: pd.DataFrame):
    """
    Évolution du nombre de cas par année.
    """
    if "Year" not in df.columns or "ID" not in df.columns:
        print("⚠ Colonnes 'Year' ou 'ID' manquantes.")
        return

    plt.figure(figsize=(8, 4))
    df.groupby("Year")["ID"].count().plot(kind="line", marker="o")
    plt.title("Évolution des cas par année")
    plt.ylabel("Nombre de cas")
    plt.tight_layout()
    plt.show()


def plot_department_load(df: pd.DataFrame):
    """
    Nombre de cas par département.
    """
    if "Department" not in df.columns:
        print("⚠ 'Department' non présent dans le DataFrame.")
        return

    plt.figure(figsize=(10, 5))
    df["Department"].value_counts().plot(kind="bar", color="orange")
    plt.title("Charge de travail par département")
    plt.ylabel("Nombre de cas")
    plt.tight_layout()
    plt.show()


def plot_heatmap_patho_anatomy(df: pd.DataFrame):
    """
    Heatmap Pathologie × Anatomie basée sur les colonnes classiques :
        - Diagnosis
        - Anatomy
    Si l'une des colonnes est absente → la fonction affiche un message.
    """
    if "Diagnosis" not in df.columns or "Anatomy" not in df.columns:
        print("⚠ 'Diagnosis' ou 'Anatomy' manquant(e) pour la heatmap.")
        return

    pivot = pd.crosstab(df["Diagnosis"], df["Anatomy"])

    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, cmap="Blues")
    plt.title("Heatmap Pathologie × Anatomie (Diagnosis × Anatomy)")
    plt.tight_layout()
    plt.show()


# =============================================================================
# 3️⃣ Data Quality (DQ)
# =============================================================================

def plot_missing_values(df: pd.DataFrame):
    """
    Barplot du nombre de valeurs manquantes par colonne.
    """
    plt.figure(figsize=(10, 5))
    df.isna().sum().plot(kind="bar", color="red")
    plt.title("Taux de valeurs manquantes")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


def plot_description_length(df: pd.DataFrame):
    """
    Distribution de la longueur de la description clinique.
    """
    desc = df.get("Description", "").astype(str)
    df = df.copy()
    df["DescLen"] = desc.apply(len)

    plt.figure(figsize=(8, 4))
    sns.histplot(df["DescLen"], bins=20, color="green")
    plt.title("Distribution de la longueur de la Description clinique")
    plt.tight_layout()
    plt.show()


def plot_birthdate_vs_date(df: pd.DataFrame):
    """
    Vérifie la cohérence entre Birthdate et Date via l'âge recalculé.
    """
    if "Date" not in df.columns or "Birthdate" not in df.columns:
        print("⚠ 'Date' ou 'Birthdate' manquante pour la cohérence âge.")
        return

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
    df["Birthdate"] = pd.to_datetime(df["Birthdate"], errors="coerce", dayfirst=True)

    df["AgeComputed"] = df["Date"].dt.year - df["Birthdate"].dt.year

    plt.figure(figsize=(8, 4))
    sns.histplot(df["AgeComputed"].dropna(), kde=True)
    plt.title("Vérification cohérence Birthdate (Age recalculé)")
    plt.tight_layout()
    plt.show()


# =============================================================================
# 4️⃣ Analyses avancées
# =============================================================================

def kmeans_segmentation(df: pd.DataFrame, n: int = 4):
    """
    Segmentation simple des patients via KMeans sur l'âge.
    """
    if "Age" not in df.columns:
        print("⚠ 'Age' non présent dans le DataFrame.")
        return

    X = df[["Age"]].dropna().copy()
    if X.empty:
        print("⚠ Aucun âge disponible pour KMeans.")
        return

    model = KMeans(n_clusters=n, random_state=42, n_init="auto")
    X["cluster"] = model.fit_predict(X)

    plt.figure(figsize=(8, 4))
    sns.scatterplot(data=X, x=X.index, y="Age", hue="cluster", palette="tab10")
    plt.title("Segmentation des patients par âge (KMeans)")
    plt.tight_layout()
    plt.show()


def word_cooccurrence_graph(df: pd.DataFrame):
    """
    Placeholder pour une future analyse NLP de co-occurrences de mots.
    """
    print("⚠ Fonction simplifiée : graph de co-occurrence NLP à implémenter si besoin.")
