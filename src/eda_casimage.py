"""
================================================================================
                   EDA (Exploratory Data Analysis) – CASIMAGE
                Version Professionnelle Premium — Documentation GitHub
================================================================================

Objectifs du script :
    ✔ Charger le dataset nettoyé produit par clean_data.py
    ✔ Réaliser une analyse exploratoire complète (EDA)
    ✔ Générer graphiques : diagnostics, âges, tranches d’âge, départements, etc.
    ✔ Analyser la qualité des données (Description, Age, Sex…)
    ✔ Produire un radar de qualité des données
    ✔ Exporter un rapport texte dans /output/reports/

Entrée :
    output/casimage_ai_clean.csv

Sorties :
    - Graphiques interactifs (via matplotlib / seaborn)
    - Fichier texte renseignant les indicateurs EDA :
        ➜ output/reports/eda_summary.txt

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Version : 2025
================================================================================
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from math import pi
from config import CLEAN_CSV_PATH, REPORT_DIR

# Style graphique professionnel
plt.style.use("seaborn-v0_8")

DATA_PATH = CLEAN_CSV_PATH


# =============================================================================
# 1️⃣ Chargement du fichier nettoyé
# =============================================================================
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        "❌ 'casimage_ai_clean.csv' introuvable.\n"
        "Veuillez exécuter main.py puis clean_data.py avant l'EDA."
    )

df = pd.read_csv(DATA_PATH)
print(f"✔ Dataset chargé : {df.shape[0]} lignes – {df.shape[1]} colonnes\n")


# =============================================================================
# 2️⃣ Ajout d'un identifiant unique si manquant
# =============================================================================
if "ID" not in df.columns:
    df["ID"] = df.index + 1
    print("⚠️ 'ID' manquant → généré automatiquement.")
else:
    print("✔ Identifiant 'ID' détecté.")


# =============================================================================
# 3️⃣ Normalisation des types (sécurité)
# =============================================================================
df["Age"] = pd.to_numeric(df.get("Age"), errors="coerce")
df["Date"] = pd.to_datetime(df.get("Date"), errors="coerce", dayfirst=True)
df["Year"] = df["Date"].dt.year

print("🧪 Types normalisés.\n")


# =============================================================================
# 4️⃣ Aperçu global console
# =============================================================================
print("🔹 Colonnes :", list(df.columns), "\n")
print(df.info(), "\n")


# =============================================================================
# 5️⃣ Visualisation — Top diagnostics
# =============================================================================
if "Diagnosis" in df.columns:
    plt.figure(figsize=(10, 5))
    df["Diagnosis"].value_counts().head(10).plot(kind='bar', color='steelblue')
    plt.title("Top 10 diagnostics")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# =============================================================================
# 6️⃣ Distribution des âges + répartition par tranche
# =============================================================================
if "Age" in df.columns:
    # Histogramme des âges
    plt.figure(figsize=(8, 4))
    sns.histplot(df["Age"].dropna(), bins=20, kde=True, color='teal')
    plt.title("Distribution des âges")
    plt.tight_layout()
    plt.show()

    # Groupes d’âge
    df["AgeGroup"] = pd.cut(
        df["Age"],
        bins=[0, 20, 40, 60, 80, 120],
        labels=["0–20", "21–40", "41–60", "61–80", "80+"],
        right=False
    )

    plt.figure(figsize=(8, 4))
    df["AgeGroup"].value_counts().sort_index().plot(kind='bar', color="purple")
    plt.title("Répartition par tranche d’âge")
    plt.tight_layout()
    plt.show()


# =============================================================================
# 7️⃣ Départements (volume de cas)
# =============================================================================
if "Department" in df.columns:
    plt.figure(figsize=(10, 4))
    df["Department"].value_counts().plot(kind='bar', color='orange')
    plt.title("Répartition des cas par département")
    plt.tight_layout()
    plt.show()


# =============================================================================
# 8️⃣ Nombre de cas par année
# =============================================================================
if "Year" in df.columns:
    yearly = df["Year"].dropna().astype(int).value_counts().sort_index()

    plt.figure(figsize=(8, 4))
    plt.plot(yearly.index, yearly.values, marker="o")
    plt.title("Nombre de cas par année")
    plt.tight_layout()
    plt.show()


# =============================================================================
# 9️⃣ Analyse qualitative des descriptions cliniques
# =============================================================================
df["DescLen"] = df["Description"].astype(str).apply(len)

plt.figure(figsize=(8, 4))
sns.histplot(df["DescLen"], bins=20, color="brown")
plt.title("Longueur des descriptions cliniques")
plt.tight_layout()
plt.show()

n_short = (df["DescLen"] < 15).sum()
print(f"Descriptions < 15 caractères : {n_short}")


# =============================================================================
# 🔟 Radar de qualité des données
# =============================================================================
metrics = {
    "Age": df["Age"].notna().mean() * 100,
    "Diagnosis": df["Diagnosis"].notna().mean() * 100,
    "Department": df["Department"].notna().mean() * 100,
    "Sex": df["Sex"].notna().mean() * 100,
    "Description Qualité": (df["DescLen"] > 20).mean() * 100
}

labels = list(metrics.keys())
values = list(metrics.values())

# Boucle pour fermer le polygone du radar
values += values[:1]
angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
angles += angles[:1]

plt.figure(figsize=(7, 7))
ax = plt.subplot(111, polar=True)
plt.xticks(angles[:-1], labels)

ax.plot(angles, values, linewidth=2)
ax.fill(angles, values, alpha=0.3)
plt.title("Radar de Qualité des Données – CASIMAGE")
plt.show()


# =============================================================================
# 1️⃣1️⃣ Export du rapport texte
# =============================================================================
os.makedirs(REPORT_DIR, exist_ok=True)

summary_path = os.path.join(REPORT_DIR, "eda_summary.txt")

with open(summary_path, "w", encoding="utf-8") as f:
    f.write("=== RAPPORT EDA CASIMAGE (Pro Premium) ===\n\n")
    f.write(f"Lignes : {len(df)}\n")
    f.write(f"Colonnes : {len(df.columns)}\n\n")

    f.write("Top diagnostics :\n")
    f.write(str(df["Diagnosis"].value_counts().head(10)) + "\n\n")

    f.write("Départements :\n")
    f.write(str(df["Department"].value_counts()) + "\n\n")

    f.write("Qualité des descriptions :\n")
    f.write(str(df["DescLen"].describe()) + "\n\n")

print(f"\n📝 Rapport sauvegardé → {summary_path}")
print("✨ EDA terminé avec succès.\n")
