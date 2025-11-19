"""
===============================================================================
                AI-BASED XML → TABLE MAPPING (CASIMAGE ETL)
===============================================================================

Ce module génère automatiquement un *mapping JSON* entre les balises XML
et un schéma tabulaire exploitable (CSV / Data Warehouse).

Modes :
    1) Mode Offline :
         - utilise seulement la structure du XML
         - infère les types (string, int, float, date)
         - produit un mapping minimal standardisé

    2) Mode OpenAI :
         - si OPENAI_API_KEY est disponible
         - propose un mapping optimisé via LLM (GPT)

Ce composant est utilisé par :
    - main.py  → génération mapping automatique
    - dw_model.py → création de schéma Data Warehouse

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Version : 2025
===============================================================================
"""

import os
import json
import re
from typing import Dict, List, Tuple, Any


# =============================================================================
# 1️⃣ INFÉRENCE DE TYPES : _infer_types_from_samples
# -----------------------------------------------------------------------------
# Objectif :
#   - Recevoir une liste [(tag, valeur), ...]
#   - Nettoyer les noms
#   - Déduire un type simple : string / int / float / date
#   - Générer un mapping JSON minimal et propre
# =============================================================================

def _infer_types_from_samples(samples: List[Tuple[str, str]]) -> str:
    """
    Mode offline : déduit un mapping JSON simple à partir de tags et exemples.

    Paramètres
    ----------
    samples : List[(tag, value)]
        Exemple de paires (balise → valeur) pour deviner le type.

    Retour
    ------
    str
        Mapping JSON formaté (string)
    """
    import datetime as dt

    schema: Dict[str, str] = {}

    for raw_tag, value in samples:
        # Normalisation nom de colonne : letters, digits, underscore
        key = re.sub(r"[^A-Za-z0-9_]+", "_", raw_tag.strip())
        key = key.strip("_").lower() or "unknown"

        # Type par défaut
        detected_type = "string"
        cleaned_val = (value or "").strip()

        if cleaned_val:
            # Integer
            if re.fullmatch(r"-?\d+", cleaned_val):
                detected_type = "int"

            # Float
            elif re.fullmatch(r"-?\d+\.\d+", cleaned_val):
                detected_type = "float"

            # ISO Date
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", cleaned_val):
                try:
                    dt.date.fromisoformat(cleaned_val)
                    detected_type = "date"
                except Exception:
                    pass

        schema[key] = detected_type

    # Génération du JSON final
    mapping = {
        "target_table": "casimage_cases",
        "columns": [
            {
                "name": col_name,
                "type": col_type,
                "source_xpath": f"//{col_name}"
            }
            for col_name, col_type in sorted(schema.items())
        ],
    }

    return json.dumps(mapping, ensure_ascii=False, indent=2)


# =============================================================================
# 2️⃣ PROPOSITION DE MAPPING PAR IA : ai_propose_mapping
# -----------------------------------------------------------------------------
# - Si OPENAI_API_KEY absent → fallback local (offline mode)
# - Sinon → prompt GPT générant automatiquement un JSON propre
# =============================================================================

def ai_propose_mapping(structure_summary: str, model_hint: str | None = None) -> str:
    """
    Génère un mapping JSON à partir du résumé structurel d'un XML.

    Paramètres
    ----------
    structure_summary : str
        Résumé hiérarchique du XML (voir summarize_xml_structure)
    model_hint : Optional[str]
        Modèle OpenAI optionnel (fallback : gpt-4o-mini)

    Retour
    ------
    str
        Un mapping JSON (string)
    """
    api_key = os.getenv("OPENAI_API_KEY")

    # -------------------------------------------------------------------------
    # MODE OFFLINE — Aucun accès OpenAI → fallback simple et robuste
    # -------------------------------------------------------------------------
    if not api_key:
        tags = []
        for line in structure_summary.splitlines():
            match = re.search(r"-\s+([A-Za-z0-9:_-]+)\s+\(", line)
            if match:
                tags.append(match.group(1))

        # On génère des échantillons artificiels
        samples = [
            (t, "123" if "id" in t.lower() else "text")
            for t in tags[:30]  # limite sécurité
        ]

        return _infer_types_from_samples(samples)

    # -------------------------------------------------------------------------
    # MODE IA — OpenAI GPT
    # -------------------------------------------------------------------------
    try:
        from openai import OpenAI
        client = OpenAI()

        model = os.getenv("OPENAI_MODEL", model_hint or "gpt-4o-mini")

        prompt = f"""
Tu es un expert Data Engineer.
À partir du résumé XML fourni ci-dessous, produis un MAPPING JSON STRICT.

Format attendu :
{{
  "target_table": "casimage_cases",
  "columns": [
    {{
      "name": "snake_case_name",
      "type": "string|int|float|date",
      "source_xpath": "//TagName"
    }}
  ]
}}

Résumé XML :
{structure_summary[:4000]}

Réponds UNIQUEMENT avec le JSON.
"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        content = response.choices[0].message.content.strip()

        # Extraire seulement la partie JSON
        match = re.search(r"\{.*\}", content, re.S)
        return match.group(0) if match else content

    except Exception:
        # Sécurité MAX : fallback très simple
        return _infer_types_from_samples([("id", "1"), ("diagnosis", "text")])


# =============================================================================
# 3️⃣ APPLICATION D’UN MAPPING SUR UN DICT XML : apply_mapping_to_record
# -----------------------------------------------------------------------------
# Transforme un dict xmltodict en ligne tabulaire selon les XPaths du mapping.
# =============================================================================

def apply_mapping_to_record(record: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applique un mapping JSON sur un dict issu du parsing XML.

    Paramètres
    ----------
    record : dict
        Dictionnaire construit par xmltodict
    mapping : dict
        Mapping JSON déjà parsé (dict)

    Retour
    ------
    dict
        Ligne prête à être insérée dans un DataFrame / Table
    """

    # -------------------------------------------------------------------------
    # Sous-fonction : extraction via XPath simplifié
    # -------------------------------------------------------------------------
    def get_by_xpath(node: Any, xpath: str):
        """
        Parcourt un dictionnaire XML via un XPath simplifié de type //A/B/C.

        Limitation volontaire :
            - sans filtres
            - insensible à la casse
        """
        keys = [k for k in xpath.strip("/").split("/") if k]

        current = node
        for key in keys:
            if isinstance(current, list):
                current = current[0] if current else None

            if not isinstance(current, dict):
                return None

            # Match insensible à la casse + suffixe
            next_val = next(
                (v for k2, v in current.items() if k2.lower() == key.lower()),
                None
            )

            current = next_val
            if current is None:
                return None

        # Si encore une liste → récupérer premier élément
        if isinstance(current, list):
            return current[0] if current else None

        return current

    # -------------------------------------------------------------------------
    # Construction de la ligne tabulaire finale
    # -------------------------------------------------------------------------
    row = {}

    for col in mapping.get("columns", []):
        name = col.get("name")
        typ = col.get("type", "string")
        xp = col.get("source_xpath", "")

        # Extraction XML
        raw = get_by_xpath(record, xp) if xp else None
        val = str(raw) if raw is not None else None

        # Conversion typée
        try:
            if val is None:
                row[name] = None
            elif typ == "int":
                row[name] = int(val)
            elif typ == "float":
                row[name] = float(val)
            else:
                row[name] = val
        except Exception:
            row[name] = None

    return row
