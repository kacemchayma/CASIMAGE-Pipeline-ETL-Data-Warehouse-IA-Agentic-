"""
===============================================================================
                        🚀 CASIMAGE – Pipeline Professionnel
                Extraction → Nettoyage → Star Schema → Data Warehouse
-------------------------------------------------------------------------------
Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Description :
    Pipeline complet :
        ✔ Extraction ZIP
        ✔ Parsing XML → DataFrame
        ✔ Nettoyage avancé (Age, Sexe, Texte…)
        ✔ Export CSV + Parquet
        ✔ Construction du Star Schema
        ✔ Chargement dans MySQL (XAMPP) ou SQLite fallback
===============================================================================
"""

# =============================================================================
# Imports
# =============================================================================

import os
import glob
import json
import shutil
import xmltodict
import pandas as pd
from dotenv import load_dotenv

from transform_utils import clean_xml_text, flatten_qcm
from xml_utils import unzip_to_folder, summarize_xml_structure
from enhanced_cleaning import apply_enhanced_cleaning
from dw_model import (
    build_star_schema,
    load_star_schema_sqlite,
    load_star_schema_mysql
)
from config import (
    DATA_DIR, EXTRACT_DIR, OUTPUT_DIR,
    CSV_PATH, DB_PATH
)


# =============================================================================
# Initialisation
# =============================================================================

load_dotenv()
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Nettoyage du dossier EXTRACT
shutil.rmtree(EXTRACT_DIR, ignore_errors=True)


# =============================================================================
# 1️⃣ Extraction ZIP
# =============================================================================

zip_files = glob.glob(os.path.join(DATA_DIR, "*.zip"))
if not zip_files:
    raise SystemExit("❌ Aucun fichier ZIP trouvé dans data/.")

zip_path = zip_files[0]
print(f"📦 ZIP détecté : {os.path.basename(zip_path)}")

xml_files = unzip_to_folder(zip_path, EXTRACT_DIR)
print(f"✅ {len(xml_files)} fichiers XML extraits.\n")

if not xml_files:
    raise SystemExit("❌ Extraction échouée : aucun XML trouvé.")


# =============================================================================
# 2️⃣ Analyse de structure XML
# =============================================================================

sample = xml_files[0]
summary = summarize_xml_structure(sample)

print(f"🔍 Exemple analysé : {os.path.basename(sample)}")
print(summary[:500], "...\n")


# =============================================================================
# 3️⃣ Lecture XML → DataFrame
# =============================================================================

rows = []

for path in xml_files:
    try:
        with open(path, "r", encoding="iso-8859-1", errors="ignore") as f:
            raw = clean_xml_text(f.read())
            data = xmltodict.parse(raw)

        case = data.get("CASIMAGE_CASE", {})

        record = {k: v for k, v in case.items() if isinstance(v, str)}
        record["QCMs"] = flatten_qcm(case)
        record["SourceFile"] = os.path.basename(path)

        rows.append(record)

    except Exception as e:
        print(f"⚠️ Erreur parsing {os.path.basename(path)} : {e}")


if not rows:
    raise SystemExit("❌ Aucun XML valide n’a pu être converti.")

df = pd.DataFrame(rows)
print(f"📊 {len(df)} lignes extraites avant nettoyage.\n")


# =============================================================================
# 4️⃣ Nettoyage basique
# =============================================================================

df.drop_duplicates(inplace=True)
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.replace({"": None, " ": None}, inplace=True)


# =============================================================================
# 5️⃣ Nettoyage avancé (Age, Sexe, Texte…)
# =============================================================================

print("🧠 Nettoyage avancé...")
df = apply_enhanced_cleaning(df)


# =============================================================================
# 6️⃣ Export CSV + Parquet
# =============================================================================

csv_path = CSV_PATH
parquet_path = os.path.join(OUTPUT_DIR, "casimage_clean.parquet")

df.to_csv(csv_path, index=False, encoding="utf-8")
df.to_parquet(parquet_path, index=False)

print("💾 Export terminé :")
print(f"→ CSV      : {csv_path}")
print(f"→ Parquet  : {parquet_path}\n")


# =============================================================================
# 7️⃣ Construction du Star Schema
# =============================================================================

print("⭐ Construction du Star Schema…")
star = build_star_schema(df)


# =============================================================================
# 8️⃣ Chargement dans Data Warehouse (MySQL → fallback SQLite)
# =============================================================================

MYSQL_URI = os.getenv("MYSQL_URI", "").strip()

if MYSQL_URI:
    print("🌐 Tentative de chargement dans MySQL (XAMPP)…")
    try:
        load_star_schema_mysql(star, MYSQL_URI)
        print("✅ DW MySQL mis à jour !")
    except Exception as e:
        print(f"⚠️ MySQL indisponible : {e}")
        print("➡️ Utilisation automatique de SQLite.")
        load_star_schema_sqlite(star, DB_PATH)
else:
    print("ℹ️ Aucun MYSQL_URI défini → SQLite utilisé.")
    load_star_schema_sqlite(star, DB_PATH)

print(f"🏥 Data Warehouse mis à jour : {DB_PATH}\n")


# =============================================================================
# 9️⃣ Nettoyage final
# =============================================================================

shutil.rmtree(EXTRACT_DIR, ignore_errors=True)
print("🧹 Dossier EXTRACT supprimé.")

print("\n🏁 Pipeline CASIMAGE terminé avec succès.")
