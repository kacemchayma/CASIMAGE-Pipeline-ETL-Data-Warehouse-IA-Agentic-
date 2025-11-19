"""
===============================================================================
                         UTILITAIRES XML — CASIMAGE ETL
===============================================================================

Ce module contient les fonctions de manipulation XML nécessaires au pipeline :

    • Extraction du ZIP → dossiers temporaires
    • Détection automatique des fichiers XML
    • Résumé hiérarchique intelligent de la structure XML

Utilisé dans main.py pour comprendre la structure des fichiers CASIMAGE.

Auteurs :
    • KACEM Chayma
    • NECHI Zeinab
    • HAMMAMI Emir

Version : 2025
===============================================================================
"""

import os
import zipfile
import glob
import xml.etree.ElementTree as ET
from collections import defaultdict


# =============================================================================
# 1️⃣ Extraction : unzip_to_folder
# -----------------------------------------------------------------------------
# Objectif :
#   - Dézipper un fichier casimage_FR.zip
#   - Créer le dossier d’extraction si nécessaire
#   - Retourner la liste des chemins XML extraits (récursif)
# =============================================================================

def unzip_to_folder(zip_path: str, extract_folder: str) -> list[str]:
    """
    Dézippe un fichier ZIP et retourne la liste des fichiers XML extraits.

    Paramètres
    ----------
    zip_path : str
        Chemin du fichier ZIP (ex: data/casimage_FR.zip)
    extract_folder : str
        Dossier cible où extraire les XML

    Retour
    ------
    list[str]
        Chemins complets vers les fichiers XML trouvés
    """
    # Création du dossier temporaire si nécessaire
    os.makedirs(extract_folder, exist_ok=True)

    # Extraction ZIP → extract_folder
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_folder)

    # Recherche récursive des fichiers XML extraits
    xml_files = glob.glob(os.path.join(extract_folder, "**", "*.xml"), recursive=True)
    return xml_files


# =============================================================================
# 2️⃣ Analyse structure : summarize_xml_structure
# -----------------------------------------------------------------------------
# Objectif :
#   - Lire un XML et produire un résumé lisible :
#
#       - TAG racine
#       - profondeur des balises
#       - nombre d'occurrences par niveau
#
#   Très utile pour deviner un schéma ou construire un mapping JSON.
# =============================================================================

def summarize_xml_structure(xml_path: str, max_nodes: int = 5000) -> str:
    """
    Analyse un XML et retourne un résumé hiérarchique des balises.

    Paramètres
    ----------
    xml_path : str
        Chemin du fichier XML à analyser
    max_nodes : int
        Borne supérieure pour éviter une explosion récursive

    Retour
    ------
    str
        Une représentation textuelle simple :
            - TAG1 (x occurrences)
            -   TAG1.1 (x occurrences)
            -   TAG1.2 (x occurrences)
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        return f"Erreur lors du parsing XML : {e}"

    counts = defaultdict(int)

    def explore(elem, depth=0, seen=None):
        """
        Parcours récursif pour compter les tags et mesurer la profondeur.
        On utilise un compteur `seen` pour limiter la profondeur réelle.
        """
        if seen is None:
            seen = [0]

        if seen[0] >= max_nodes:
            return

        # Comptage du tag
        counts[(elem.tag, depth)] += 1
        seen[0] += 1

        # Parcours des enfants
        for child in elem:
            explore(child, depth + 1, seen)

    # Déclenche l’analyse
    explore(root)

    # Formatage du rendu final
    lines = [
        f"{'  ' * depth}- {tag} ({count} occurrences)"
        for (tag, depth), count in sorted(counts.items(), key=lambda x: (x[0][1], x[0][0]))
    ]

    return "\n".join(lines)
