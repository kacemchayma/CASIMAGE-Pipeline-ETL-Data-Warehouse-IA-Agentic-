"""
===============================================================================
                    CONFIGURATION GLOBALE — CASIMAGE ETL PIPELINE
===============================================================================

Ce module centralise *tous* les chemins, constantes et paramètres généraux
utilisés dans le pipeline CASIMAGE :

    Extraction ZIP  →  Parsing XML  →  Nettoyage avancé  →
    Normalisation NLP  →  Data Warehouse (Star Schema)  →
    Analytics / Dashboard

Objectifs :
    - Centraliser les chemins et fichiers utilisés dans toutes les étapes
    - Simplifier les modifications lors du déploiement (local / serveur)
    - Garantir une exécution stable, cohérente et maintenable

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Année : 2025
===============================================================================
"""

import os


# =============================================================================
# 1️⃣ RÉPERTOIRE RACINE DU PROJET
# -----------------------------------------------------------------------------
# Exemple : /Users/user/casimage_project
# On remonte un niveau par rapport au répertoire où se trouve ce fichier.
# =============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# =============================================================================
# 2️⃣ DÉFINITION DES RÉPERTOIRES PRINCIPAUX
# -----------------------------------------------------------------------------
# DATA_DIR      → contient le ZIP casimage_FR.zip
# EXTRACT_DIR   → extraction temporaire des XML (supprimé en fin de pipeline)
# OUTPUT_DIR    → contient les fichiers résultats finaux (CSV, Parquet, DB)
# REPORT_DIR    → dossiers des rapports EDA / logs
# =============================================================================

DATA_DIR = os.path.join(BASE_DIR, "data")
EXTRACT_DIR = os.path.join(BASE_DIR, "data_temp")     # Temporaire (clean auto)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_DIR = os.path.join(OUTPUT_DIR, "reports")


# =============================================================================
# 3️⃣ FICHIERS CLÉS DU PIPELINE CASIMAGE
# -----------------------------------------------------------------------------
# ZIP_NAME         : archive XML d'origine CASIMAGE
# CSV_PATH         : aplat XML → CSV brut
# CLEAN_CSV_PATH   : CSV nettoyé (EDA + Dashboard)
# DB_PATH          : Data Warehouse SQLite
# =============================================================================

ZIP_NAME = "casimage_FR.zip"

CSV_PATH = os.path.join(OUTPUT_DIR, "casimage_ai.csv")
CLEAN_CSV_PATH = os.path.join(OUTPUT_DIR, "casimage_ai_clean.csv")

DB_PATH = os.path.join(OUTPUT_DIR, "casimage_dw.db")


# =============================================================================
# 4️⃣ CRÉATION AUTOMATIQUE DES DOSSIERS
# -----------------------------------------------------------------------------
# On crée uniquement les dossiers finaux. data_temp sera généré puis supprimé.
# =============================================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 🎯 Fin du fichier — Ce module ne contient que des constantes.
# -----------------------------------------------------------------------------
