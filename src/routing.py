"""
Jour 3 - Objectif: Optimiser l'ordre de visite des emplacements pour chaque agent
"""

from typing import List, Set
from src.models import Product, Location, Agent


def extract_unique_locations(products: List[Product]) -> Set[Location]:
    """
    Extrait les emplacements uniques d'une liste de produits.
    
    Cette fonction prend une liste de produits et retourne UNIQUEMENT les emplacements 
    où ces produits sont situés (sans doublons). C'est la première étape de la modélisation TSP.
    
    """
    # Créer un ensemble vide 
    unique_locations = set()
    
    # Parcourir chaque produit et ajouter son emplacement au Set
    # Le Set supprime automatiquement les doublons grâce à __hash__() et __eq__()
    for product in products:
        unique_locations.add(product.location)
    
    return unique_locations
