"""
===============================================================================
                     🚀 CASIMAGE – Orchestrateur de Pipeline ETL
-------------------------------------------------------------------------------
Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Description :
    Ce script orchestre toute la chaîne de traitement CASIMAGE :

        1) Extraction XML → CSV (main.py)
        2) Nettoyage complémentaire pour EDA (clean_data.py)
        3) Analyse statistique descriptive (eda_casimage.py)
        4) Analytics avancés (analytics.py) – optionnel
        5) Dashboard interactif (eda_dashboard.py)

Notes :
    - Les étapes 3 et 4 sont “allow_fail=True” car elles peuvent nécessiter
      des librairies externes (sklearn, seaborn…) non obligatoires.
    - Le dashboard reste optionnel (lancement manuel possible).

===============================================================================
"""

import subprocess
import sys
import os


# =============================================================================
# 1️⃣ Définition des chemins
# =============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")


# =============================================================================
# 2️⃣ Fonction générique de lancement d'étape
# =============================================================================

def run(step: str, script: str, allow_fail: bool = False):
    """
    Exécute un script Python du dossier /src dans un sous-processus.

    Paramètres
    ----------
    step : str
        Nom lisible de l'étape affiché à l'écran.
    script : str
        Nom du fichier Python à lancer.
    allow_fail : bool
        Si False → le pipeline s'arrête en cas d'erreur.
        Si True  → on continue quand même (utile pour modules optionnels).
    """
    print(f"\n🔷 {step}")
    script_path = os.path.join(SRC_DIR, script)

    if not os.path.exists(script_path):
        print(f"❌ Script introuvable : {script_path}")
        if not allow_fail:
            raise FileNotFoundError(script_path)
        return

    try:
        subprocess.run(
            [sys.executable, script_path],
            check=True
        )
        print("✅ Terminé.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec durant : {script}")
        print(f"📌 Détails : {e}\n")
        if not allow_fail:
            raise e
        else:
            print("⚠️ Étape ignorée car allow_fail=True.")


# =============================================================================
# 3️⃣ Orchestration complète
# =============================================================================

if __name__ == "__main__":

    print("\n🚀 Lancement du pipeline complet CASIMAGE (ETL + Nettoyage + DQ + Dashboard)…")

    try:
        # ----------------------------------------------------------------------
        # ÉTAPE 1 – EXTRACT → TRANSFORM → LOAD dans Data Warehouse
        # ----------------------------------------------------------------------
        run("Étape 1 : Extraction → Transformation → Stockage DW", "main.py")

        # ----------------------------------------------------------------------
        # ÉTAPE 2 – Nettoyage complémentaire pour EDA
        # ----------------------------------------------------------------------
        run("Étape 2 : Nettoyage complémentaire pour l'EDA", "clean_data.py")

        # ----------------------------------------------------------------------
        # ÉTAPE 3 – Analyse descriptive (EDA Statique)
        # ----------------------------------------------------------------------
        run("Étape 3 : Analyse descriptive (EDA statique)", "eda_casimage.py",
            allow_fail=True)

        # ----------------------------------------------------------------------
        # ÉTAPE 4 – Analytics avancés (Clustering, Data Quality, NLP)
        # ----------------------------------------------------------------------
        run("Étape 4 : Analytics avancés (DQ + NLP + Clustering)", "analytics.py",
            allow_fail=True)

        # ----------------------------------------------------------------------
        # ÉTAPE 5 – Dashboard interactif
        # ----------------------------------------------------------------------
        print("\n💻 Étape 5 : Lancement du Dashboard interactif")
        print("📌 Adresse locale : http://127.0.0.1:8050")
        print("📌 Ctrl + C pour arrêter le dashboard\n")

        subprocess.run(
            [sys.executable, os.path.join(SRC_DIR, "eda_dashboard.py")],
            check=False
        )

        print("\n🏁 Pipeline CASIMAGE exécuté avec succès !")
        print("📁 Résultats disponibles dans : /output\n")

    except KeyboardInterrupt:
        print("\n🛑 Pipeline stoppé manuellement.")
    except Exception as e:
        print(f"\n⚠️ Erreur inattendue : {e}\n")
