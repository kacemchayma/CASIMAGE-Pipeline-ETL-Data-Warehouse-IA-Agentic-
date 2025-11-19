"""
===============================================================================
                    TRANSFORMATIONS XML → TEXTE — CASIMAGE ETL
===============================================================================

Ce module fournit deux fonctions essentielles au pipeline :

    1) clean_xml_text   → normalise et nettoie le contenu XML
    2) flatten_qcm      → transforme les sections QCM du XML en texte lisible

Ces transformations sont utilisées dans main.py pour convertir efficacement les
structures XML complexes de CASIMAGE vers un format tabulaire propre.

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Version : 2025
===============================================================================
"""

import re


# =============================================================================
# 1️⃣ Nettoyage XML : clean_xml_text
# -----------------------------------------------------------------------------
# Convertit :
#   - entités HTML (&eacute;, &amp;, etc.)
#   - entités numériques (&#233;)
#   - supprime espaces multiples et artefacts
# Objectif : obtenir un texte propre avant passage à xmltodict / NLP.
# =============================================================================
def clean_xml_text(raw: str) -> str:
    """
    Nettoie un texte XML en remplaçant les entités HTML, les entités numériques
    et en supprimant les espaces superflus.

    Paramètres
    ----------
    raw : str
        Contenu XML original (souvent encodé ISO-8859-1)

    Retour
    ------
    str
        Texte normalisé et nettoyé
    """
    if not isinstance(raw, str):
        return ""

    # Entités HTML les plus courantes dans CASIMAGE
    replacements = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
        "&lt;": "<",
        "&gt;": ">",
        "&eacute;": "é",
        "&ecirc;": "ê",
        "&egrave;": "è",
        "&agrave;": "à",
        "&ccedil;": "ç",
        "&ocirc;": "ô",
    }

    # Remplacement direct des entités textuelles
    for old, new in replacements.items():
        raw = raw.replace(old, new)

    # Conversion des entités numériques ex : &#233;
    raw = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), raw)

    # Normalisation des espaces
    raw = re.sub(r"\s+", " ", raw)

    return raw.strip()


# =============================================================================
# 2️⃣ Aplatissement QCM : flatten_qcm
# -----------------------------------------------------------------------------
# Le XML CASIMAGE contient parfois plusieurs formats :
#
#   <QCM>
#       <QUESTION>...</QUESTION>
#       <ANSWERA>...</ANSWERA>
#       <ANSWERB>...</ANSWERB>
#   </QCM>
#
#   OU
#
#   <QCM>
#       <QUESTION>...</QUESTION>
#       <ANSWER1>...</ANSWER1>
#       <ANSWER2>...</ANSWER2>
#   </QCM>
#
#   OU encore :
#       <ANSWER><TEXT>...</TEXT></ANSWER>
#
# Cette fonction uniformise et concatène tout en texte lisible.
# =============================================================================
def flatten_qcm(case: dict) -> str:
    """
    Aplati les structures QCM d’un cas XML sous forme de texte lisible.

    Paramètres
    ----------
    case : dict
        Dictionnaire XML extrait via xmltodict

    Retour
    ------
    str
        Chaîne de type : "Question ? | Réponses : A; B; C || Question2 ..."
    """
    # Extraction flexible de la liste de QCM
    qcms = case.get("QCM", [])
    if not isinstance(qcms, list):
        qcms = [qcms]

    output_blocks = []

    for q in qcms:
        if not isinstance(q, dict):
            continue

        # Question principale
        question = q.get("QUESTION", "").strip()

        answers = []

        # ---------------------------------------------------------------------
        # 1) Formats classiques ANSWERA / B / C / D
        # ---------------------------------------------------------------------
        for a in ["ANSWERA", "ANSWERB", "ANSWERC", "ANSWERD"]:
            if a in q and isinstance(q[a], str) and q[a].strip():
                answers.append(q[a].strip())

        # ---------------------------------------------------------------------
        # 2) Formats alternatifs ANSWER1 / ANSWER2 / ...
        # ---------------------------------------------------------------------
        for key, value in q.items():
            if key.lower().startswith("answer") and isinstance(value, str):
                val = value.strip()
                if val and val not in answers:
                    answers.append(val)

        # ---------------------------------------------------------------------
        # 3) Format imbriqué : <ANSWER><TEXT>...</TEXT></ANSWER>
        # ---------------------------------------------------------------------
        if "ANSWER" in q and isinstance(q["ANSWER"], dict):
            txt = q["ANSWER"].get("TEXT")
            if isinstance(txt, str) and txt.strip():
                answers.append(txt.strip())

        # Si aucune réponse → indiquer vide
        answers_text = "; ".join(answers) if answers else "Aucune réponse"

        # Ajout du bloc formaté
        output_blocks.append(f"{question} | Réponses: {answers_text}")

    return " || ".join(output_blocks)
