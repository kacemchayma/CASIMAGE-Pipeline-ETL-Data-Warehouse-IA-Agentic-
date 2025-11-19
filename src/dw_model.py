# src/dw_model.py
"""
===============================================================================
                        ⭐ CASIMAGE – Data Warehouse (Star Schema)
-------------------------------------------------------------------------------
Construit les dimensions & table de faits optimales pour les données CASIMAGE.

Dimensions :
    • DimPatient
    • DimExam
    • DimPathology
    • FactCase

Compatible :
    • SQLite (local)
    • MySQL / XAMPP (via SQLAlchemy)

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir
===============================================================================
"""

import os
import sqlite3
import pandas as pd
from typing import Dict


# =============================================================================
# 1️⃣ Construction du STAR SCHEMA
# =============================================================================
def build_star_schema(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    df = df.copy()

    # -------------------- CaseNaturalKey --------------------
    df["CaseNaturalKey"] = df.get("ID", df.index).astype(str)

    # -------------------- DimPatient --------------------
    patient_cols = [c for c in ["Sex", "Age", "Birthdate", "AgeGroup"] if c in df.columns]

    dim_patient = df[patient_cols].drop_duplicates().reset_index(drop=True)
    dim_patient.insert(0, "PatientKey", dim_patient.index + 1)

    df = df.merge(dim_patient, on=patient_cols, how="left")

    # -------------------- DimExam --------------------
    exam_cols = [c for c in ["Date", "Year", "Hospital", "Department"] if c in df.columns]

    dim_exam = df[exam_cols].drop_duplicates().reset_index(drop=True)
    dim_exam.insert(0, "ExamKey", dim_exam.index + 1)

    df = df.merge(dim_exam, on=exam_cols, how="left")

    # -------------------- DimPathology --------------------
    path_cols = [
        c for c in [
            "Diagnosis", "Chapter", "Description",
            "KeyWords", "Anatomy", "Title"
        ]
        if c in df.columns
    ]

    dim_path = df[path_cols].drop_duplicates().reset_index(drop=True)
    dim_path.insert(0, "PathologyKey", dim_path.index + 1)

    df = df.merge(dim_path, on=path_cols, how="left")

    # -------------------- FactCase --------------------
    fact_case = df[
        [
            "CaseNaturalKey",
            "PatientKey",
            "ExamKey",
            "PathologyKey",
            "SourceFile",
            "ClinicalPresentation",
            "Commentary"
        ]
    ].drop_duplicates().reset_index(drop=True)

    fact_case.insert(0, "FactCaseKey", fact_case.index + 1)

    return {
        "DimPatient": dim_patient,
        "DimExam": dim_exam,
        "DimPathology": dim_path,
        "FactCase": fact_case
    }


# =============================================================================
# 2️⃣ Chargement SQLite
# =============================================================================
def load_star_schema_sqlite(tables: Dict[str, pd.DataFrame], db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)

    try:
        for name, table in tables.items():
            table.to_sql(name, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# 3️⃣ Chargement MySQL (XAMPP)
# =============================================================================
def load_star_schema_mysql(tables: Dict[str, pd.DataFrame], uri: str):
    """
    Exemple d’URI :
        mysql+pymysql://root@localhost:3306/casimage_dw

    Nécessite :
        pip install sqlalchemy pymysql
    """
    from sqlalchemy import create_engine
    engine = create_engine(uri)

    with engine.begin() as conn:
        for name, table in tables.items():
            table.to_sql(name, conn, if_exists="replace", index=False)
