# CASIMAGE-Pipeline-ETL-Data-Warehouse (IA-Agentic)

## Projet
Pipeline complet pour l’ingestion, le nettoyage, la normalisation et l’analyse des cas cliniques CASIMAGE.

---

## Fonctionnalités principales

✔ Extraction automatique des ZIP  
✔ Parsing XML robuste  
✔ Nettoyage avancé (âge, sexe, texte, métadonnées)  
✔ Module IA agentique autonome pour générer le mapping  
✔ Data Quality + transformations EDA  
✔ Star Schema professionnel  
✔ Data Warehouse (SQLite ou MySQL)  
✔ Dashboard interactif (Plotly Dash)

---

## Innovation : IA Agentic Mapping
Le module `ai_mapper.py` analyse automatiquement la structure XML et génère un mapping JSON optimisé.

Aucun schéma manuel requis → évolutif → intelligent.

---

## Architecture

```mermaid
flowchart TD

    A[ZIP CASIMAGE] --> B[Extraction ZIP]
    B --> C[Parsing XML]
    C --> D[IA Agentic Mapping]
    D --> E[DataFrame Brut]
    E --> F[Nettoyage Avancé]
    F --> G[Data Quality]
    G --> H[Star Schema DW]
    H --> I[(MySQL / SQLite)]
    G --> J[EDA]
    G --> K[Dashboard]
