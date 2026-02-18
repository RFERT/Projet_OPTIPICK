"""
Jour 3 - Objectif: Optimiser l'ordre de visite des emplacements pour chaque agent
"""

from typing import List, Set
from src.models import Product, Location, Agent
from src.utils import manhattan


def extract_unique_locations(products: List[Product]) -> Set[Location]:
    unique_locations = set()  # ← Ensemble VIDE
    
    for product in products:
        unique_locations.add(product.location)  # Ajouter l'emplacement du produit
    
    return unique_locations


def build_nodes_with_entry(entry_point: Location, unique_locations: Set[Location]) -> List[Location]:
    locations_list = list(unique_locations)  # Convertir SET en LISTE
    
    # Circuit fermé : [Entrée] + [Produits] + [Entrée]
    nodes = [entry_point] + locations_list + [entry_point]
    
    return nodes


def compute_distance_matrix(nodes: List[Location]) -> List[List[int]]:
    """
    Calcule la matrice des distances Manhattan entre tous les nœuds.
    """
    n = len(nodes)
    distance_matrix = [[0] * n for _ in range(n)]  # Matrice pré-créée de 0
    
    # Pour chaque nœud de départ
    for node_from_index in range(n):
        # Calculer uniquement les distances vers les nœuds non visités (node_to >= node_from)
        for node_to_index in range(node_from_index, n):
            # Calculer une seule fois
            distance = manhattan(nodes[node_from_index], nodes[node_to_index])
            
            # Remplir à la fois [from][to] et [to][from] (symétrie)
            distance_matrix[node_from_index][node_to_index] = distance
            distance_matrix[node_to_index][node_from_index] = distance
    
    return distance_matrix