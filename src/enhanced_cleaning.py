"""
===============================================================================
          NETTOYAGE AVANCÉ — CASIMAGE (Âge, Sexe, Texte, Métadonnées)
===============================================================================

Ce module applique un nettoyage "intelligent" sur le DataFrame produit
par le parsing XML :

    - Normalisation du texte (suppression caractères de contrôle)
    - Correction / inférence de l'Âge :
        • Age valide dans la colonne Age
        • Sinon extraction dans le texte (ClinicalPresentation, Description, Title)
        • Sinon calcul via Birthdate et Date
    - Inférence du sexe (Sex) via :
        • Mot-clés explicites (homme, femme, patiente…)
        • Anatomie / pathologies genrées (ovaire, prostate…)
    - Suppression des colonnes métadonnées "O*"
    - Suppression des lignes sans âge (Age manquant)

Utilisation :
    from enhanced_cleaning import apply_enhanced_cleaning
    df = apply_enhanced_cleaning(df)

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir
===============================================================================
"""

import re
import pandas as pd


# =============================================================================
# 0️⃣ Nettoyage générique du texte
# =============================================================================
def normalize_text(s: str) -> str:
    """
    Nettoie une chaîne :
      - supprime caractères de contrôle ASCII
      - supprime certains artefacts
      - normalise les espaces
    """
    if not isinstance(s, str):
        return ""

    # Supprimer caractères de contrôle ASCII 0–31 et 127–159
    s = re.sub(r"[\x00-\x1F\x7F-\x9F]", " ", s)

    # Supprimer artefacts visibles
    s = s.replace("***", " ")

    # Normaliser espaces multiples en un espace
    s = re.sub(r"\s+", " ", s)

    return s.strip()


# =============================================================================
# 1️⃣ Détection heuristique de l'âge
# =============================================================================

# Exemple : "Homme de 45 ans", "patient 12 ans", "16 yo"
AGE_REGEX = re.compile(r"(\b\d{1,2})\s*(ans|an|yo|years?)\b", re.IGNORECASE)

def extract_age_from_text(text: str) -> int | None:
    """
    Tente d'extraire un âge à partir d'un texte libre.
    Exclut certaines formulations ambiguës (depuis X ans, évolution...).
    """
    if not isinstance(text, str):
        return None

    text = normalize_text(text).lower()

    # ❌ Exclure "depuis 10 ans", "douleurs depuis 5 ans"
    if re.search(r"depuis\s+\d{1,2}\s+ans", text):
        return None

    # ❌ Exclure "évolution depuis X ans"
    if "évolution" in text:
        return None

    # Extraction propre
    m = AGE_REGEX.search(text)
    if m:
        age = int(m.group(1))
        if 1 <= age <= 120:
            return age
    return None


def fix_age(row: pd.Series) -> int | None:
    """
    Retourne un âge corrigé pour une ligne :
      1) Si Age valide → le garder
      2) Sinon tenter dans le texte (ClinicalPresentation, Description, Title)
      3) Sinon tenter via Birthdate + Date
    """
    age = row.get("Age", None)

    # Garder âge valide
    if pd.notna(age):
        try:
            age = int(age)
            if 1 <= age <= 120:
                return age
        except Exception:
            pass

    # Tentative via texte libre
    for col in ["ClinicalPresentation", "Description", "Title"]:
        a = extract_age_from_text(row.get(col, ""))
        if a:
            return a

    # Tentative via Birthdate + Date (année d'examen - année de naissance)
    try:
        birth = pd.to_datetime(row.get("Birthdate"), errors="coerce", dayfirst=True)
        exam = pd.to_datetime(row.get("Date"), errors="coerce", dayfirst=True)
        if pd.notna(birth) and pd.notna(exam):
            computed = exam.year - birth.year
            if 1 <= computed <= 120:
                return computed
    except Exception:
        pass

    return None


# =============================================================================
# 2️⃣ Déduction du sexe (VERSION ULTRA PRO)
# =============================================================================

SEX_PATTERNS = {
    "M": [
        r"\bhomme\b",
        r"\bgarçon\b",
        r"\bpatient\b(?!e)",   # patient mais PAS patiente
        r"\bmasculin\b",
        r"\bil présente\b",
        r"\bil consulte\b",
        r"\bil s'agit\b",
        r"\bil a\b",
        r"\ble patient\b(?!e)",
        r"\bd['’]un homme\b",
        r"\bchez lui\b",
        r"\bmr\b",
        r"\bm\.\b",
    ],

    "F": [
        r"\bfemme\b",
        r"\bfille\b",
        r"\bpatiente\b",
        r"\bpatientes\b",
        r"\bféminin\b",
        r"\belle présente\b",
        r"\belle consulte\b",
        r"\belle s'agit\b",
        r"\belle a\b",
        r"\bla patiente\b",
        r"\bd['’]une femme\b",
        r"\bchez elle\b",
        r"\bmme\b",
        r"\bmme\.\b",
        r"\bmademoiselle\b",
        r"\bmle\b",
    ],
}

# Anatomie / pathologies genrées (forts indices M/F)
SEX_KEYWORDS = {
    "M": [
        "prostate", "testicule", "scrotum", "verge",
        "pénis", "penis", "epididyme", "épididyme", "andropause"
    ],
    "F": [
        "ovaire", "ovaires", "utérus", "uterus", "grossesse",
        "endomètre", "endometre", "fœtus", "foetus",
        "ménopause", "menopause", "gynécologie", "gynecologie", "mamelle"
    ],
}

def infer_sex_from_text(text: str) -> str:
    """
    Tente de déduire le sexe (M/F) à partir d'un texte libre.
    Utilise :
      - motifs explicites (homme, patiente, etc.)
      - mots-clés anatomiques (prostate, utérus, etc.)
    """
    if not isinstance(text, str):
        return ""

    t = normalize_text(text).lower()

    # 1️⃣ Pronoms et formes explicites
    for sex, patterns in SEX_PATTERNS.items():
        for p in patterns:
            if re.search(p, t):
                return sex

    # 2️⃣ Anatomie / pathologies genrées
    for sex, kw_list in SEX_KEYWORDS.items():
        for kw in kw_list:
            if kw in t:
                return sex

    return ""


def fix_sex(row: pd.Series) -> str:
    """
    Corrige ou infère la valeur de Sex (M/F) pour une ligne du DataFrame.
    """
    val = str(row.get("Sex", "")).strip().upper()
    if val in {"M", "F"}:
        return val

    # Inspection de plusieurs colonnes textuelles
    for col in ["ClinicalPresentation", "Description", "Commentary", "Title", "KeyWords"]:
        s = infer_sex_from_text(row.get(col, ""))
        if s:
            return s

    return ""


# =============================================================================
# 3️⃣ Fonction principale : nettoyage complet
# =============================================================================
def apply_enhanced_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique le pipeline de nettoyage avancé :

        - Normalisation texte (plusieurs colonnes)
        - Correction des âges
        - Déduction du sexe
        - Suppression des colonnes O* (métadonnées techniques)
        - Suppression des lignes sans Age

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame brut après parsing XML + nettoyage basique.

    Retour
    ------
    pd.DataFrame
        DataFrame prêt pour export CSV + Data Warehouse.
    """
    df = df.copy()

    # Nettoyage léger des colonnes textuelles
    text_cols = [
        "Description", "ClinicalPresentation", "Diagnosis",
        "Title", "Commentary", "KeyWords", "Anatomy",
        "Chapter", "Hospital", "Department"
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(normalize_text)

    # Correction Age
    if "Age" in df.columns:
        df["Age"] = df.apply(fix_age, axis=1)

    # Correction Sexe
    df["Sex"] = df.apply(fix_sex, axis=1)

    # 🔥 SUPPRESSION TOTALE des colonnes métadonnées O*
    o_cols = [c for c in df.columns if c.startswith("O")]
    df.drop(columns=o_cols, inplace=True, errors="ignore")

    # 🔥 SUPPRESSION DES LIGNES SANS ÂGE (inexploitable en clinique)
    df = df[df["Age"].notna()]

    return df
