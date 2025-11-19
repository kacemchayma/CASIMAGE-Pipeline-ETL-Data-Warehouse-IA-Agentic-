# 🚀 CASIMAGE – Pipeline ETL Professionnel

**Auteur :** Data Engineering Team (Kacem Chayma – Nechi Zeinab– Hammami Emir)

---

## 📌 1. Objectif du pipeline ETL

Ce pipeline traite les cas radiologiques CASIMAGE depuis leur format brut (ZIP/XML) jusqu’à un **Data Warehouse en schéma en étoile** prêt pour la BI, le reporting et la data science.

Il réalise :

* **Extract** : Extraction ZIP → Parsing XML → Transformation structurée
* **Transform** : Nettoyage basique + nettoyage intelligent (âge, sexe, métadonnées) + enrichissement + mapping IA
* **Load** : Export CSV/Parquet + chargement Data Warehouse (SQLite/MySQL possible)

---

## 🎯 2. Architecture générale

```
/data
    └── *.zip  (CASIMAGE raw)
/src
    ├── xml_utils.py          → unzip & parsing
    ├── transform_utils.py    → flatten, text cleaning
    ├── enhanced_cleaning.py  → Age/Sex/Metadata intelligence
    ├── clean_data.py         → EDA cleaning
    ├── dw_model.py           → Star Schema builder
    ├── main.py               → Full ETL pipeline
    └── run_pipeline.py       → CLI runner
/output
    ├── casimage_ai.csv
    ├── casimage_ai.parquet
    ├── mapping_ai.json
    └── dw.sqlite (ou MySQL)
```

---

## 📥 3. Étape EXTRACT (E)

### ✔ 3.1. Extraction ZIP

* Détection automatique du fichier ZIP dans `/data`
* Extraction dans `/extract`
* Récupération de tous les fichiers `*.xml`

### ✔ 3.2. Parsing XML → Dict Python

Utilisation de :

```python
xmltodict.parse()
```

Gestion :

* encodage iso-8859-1
* nettoyage caractères illégaux
* aplatissage structure XML → lignes tabulaires

### ✔ 3.3. Extraction du QCM & structures imbriquées

`flatten_qcm()` génère un dictionnaire structuré contenant :

* items
* questions/réponses
* annotations

---

## 🔄 4. Étape TRANSFORM (T)

Transformation en **deux couches** :

### 🧹 4.1. Nettoyage basique

* suppression doublons
* trim des chaînes
* valeurs vides → `None`
* homogénéisation texte

### 🧠 4.2. Nettoyage avancé intelligent

Module : `enhanced_cleaning.py`

Fonctionnalités clés :

* **Détection automatique de l’âge** via :

  * champ Age
  * texte libre "Homme de 45 ans" (regex)
  * Birthdate + Date
* **Détection du sexe (M/F)** via :

  * mots clés explicites
  * anatomie spécifique (prostate → M, utérus → F)
* **Nettoyage métadonnées O*** (colonnes techniques inutiles)
* **Suppression lignes sans âge**

### 🛠 4.3. Conversion de types + enrichissements EDA

Module : `clean_data.py`

* Age → numérique
* Date / Birthdate → datetime
* Ajout : `Year`, `AgeGroup`

### 🤖 4.4. Mapping IA

Module : `ai_mapper.py`
Génère un mapping JSON basé sur la structure XML analysée.

---

## 🏛 5. Étape LOAD (L)

### ✔ 5.1. Export fichiers analytiques

Formats produits dans `/output` :

* `casimage_ai.csv`
* `casimage_ai.parquet`
* `mapping_ai.json`

### ⭐ 5.2. Chargement Data Warehouse (Star Schema)

Module : `dw_model.py`

Schéma en étoile construit automatiquement :

### 📂 DIM_PATIENT

* patient_id
* age
* sex

### 📂 DIM_EXAM

* exam_id
* date
* year
* anatomy
* chapter
* hospital
* department

### 📂 DIM_PATHOLOGY

* pathology_id
* diagnosis_clean

### 📂 FACT_CASE

* fact_id
* patient_id (FK)
* exam_id (FK)
* pathology_id (FK)
* keywords
* description
* clinicalPresentation

Star schema chargé par défaut dans **SQLite** mais compatible MySQL.

---

## 🚀 6. Execution totale

### CLI simple :

```bash
python src/main.py
```

Ou version orchestrée :

```bash
python src/run_pipeline.py
```

---

## 📊 7. Résultat final

À la fin du pipeline :

* DW complet
* Fichiers propres analytiques
* Star Schema consultable depuis Power BI, Tableau, Metabase, MySQL Workbench

---

## 🧱 8. Extension : connexion MySQL

Remplacement du loader SQLite dans `dw_model.py` par un loader MySQL via `mysql.connector`.
Permet intégration avec **XAMPP / phpMyAdmin**.

---

## 🏁 9. Conclusion

Ce pipeline fournit :

* un traitement robuste
* un Data Warehouse structuré
* un code modulaire & maintenable
* une architecture Data Engineer professionnelle

Ce fichier peut être placé dans :

```
src/docs/etl_pipeline.md
```
