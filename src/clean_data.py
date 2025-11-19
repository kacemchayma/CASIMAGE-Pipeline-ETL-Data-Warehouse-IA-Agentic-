"""
===============================================================================
                    NETTOYAGE COMPLÉMENTAIRE POUR L'EDA — CASIMAGE
===============================================================================

Objectif :
    - Charger le CSV brut généré par main.py (casimage_ai.csv)
    - Corriger les types (numériques, dates)
    - Ajouter colonnes dérivées (Year, AgeGroup)
    - Nettoyer les champs texte
    - Supprimer CaseID (colonne technique générée par xmltodict)
    - Produire un CSV propre pour l'exploration & dashboard

Entrée :
    output/casimage_ai.csv

Sortie :
    output/casimage_ai_clean.csv

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Version : 2025
===============================================================================
"""

import os
import pandas as pd
from config import CSV_PATH, CLEAN_CSV_PATH


# =============================================================================
# 1️⃣ Vérification de l'existence du fichier source
# =============================================================================
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(
        f"❌ Fichier introuvable : {CSV_PATH}\n"
        f"Veuillez exécuter d'abord main.py pour générer le CSV brut."
    )

print(f"📂 Chargement du dataset brut : {CSV_PATH}")
df = pd.read_csv(CSV_PATH)


# =============================================================================
# 2️⃣ Conversion des types principaux
# -----------------------------------------------------------------------------
# Age        → numérique
# Date       → datetime (exam)
# Birthdate  → datetime (naissance)
# =============================================================================
if "Age" in df.columns:
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")

if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)

if "Birthdate" in df.columns:
    df["Birthdate"] = pd.to_datetime(df["Birthdate"], errors="coerce", dayfirst=True)


# =============================================================================
# 3️⃣ Création colonne Year (année d'examen)
# =============================================================================
df["Year"] = df["Date"].dt.year if "Date" in df.columns else None


# =============================================================================
# 4️⃣ Tranches d'âge (binning)
# =============================================================================
df["AgeGroup"] = pd.cut(
    df["Age"],
    bins=[0, 20, 40, 60, 80, 120],
    labels=["0–20", "21–40", "41–60", "61–80", "80+"],
    right=False
)


# =============================================================================
# 5️⃣ Nettoyage des colonnes texte
# -----------------------------------------------------------------------------
# Remplacer NaN par "Non renseigné"
# Assurer homogénéité typage str
# =============================================================================
for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].fillna("Non renseigné")


# =============================================================================
# 6️⃣ Suppression des colonnes techniques
# -----------------------------------------------------------------------------
# CaseID est généré par xmltodict → non pertinent pour l’analyse
# =============================================================================
df.drop(columns=["CaseID"], inplace=True, errors="ignore")


# =============================================================================
# 7️⃣ Sauvegarde du CSV nettoyé
# =============================================================================
os.makedirs(os.path.dirname(CLEAN_CSV_PATH), exist_ok=True)

df.to_csv(CLEAN_CSV_PATH, index=False, encoding="utf-8")

print(f"✅ Fichier nettoyé sauvegardé : {CLEAN_CSV_PATH}")
