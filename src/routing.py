"""
Jour 3 - Objectif: Optimiser l'ordre de visite des emplacements pour chaque agent
"""
from typing import List, Set, Tuple, Callable
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


# ===== RÉSOLUTION TSP - HEURISTIQUE DU PLUS PROCHE VOISIN =====

def nearest_neighbor_tsp(
    nodes: List[Location],
    start_index: int = 0,
    distance_func: Callable[[Location, Location], int] = manhattan
) -> Tuple[List[int], int]:
    """
    Résout le TSP avec l'heuristique du Plus Proche Voisin (Nearest Neighbor).
    
    Algorithme :
        1. Commencer à l'entrée (index start_index)
        2. À chaque étape, aller à l'emplacement non visité le plus proche
        3. Répéter jusqu'à visiter tous les emplacements
        4. Retourner à l'entrée
    
    Args:
        nodes: Liste des emplacements (nœuds) à visiter
        start_index: Index du nœud de départ (0 = entrée)
        distance_func: Fonction de calcul de distance (défaut: Manhattan)
    
    Returns:
        Tuple (route_indices, total_distance) où :
        - route_indices: Liste des indices des nœuds dans l'ordre optimal
        - total_distance: Distance totale du parcours
    """
    n = len(nodes)
    unvisited = set(range(n))
    current = start_index
    route = [current]
    unvisited.remove(current)
    total_distance = 0
    
    # Visiter tous les nœuds une seule fois
    while unvisited:
        # Trouver le nœud non visité le plus proche
        nearest_index = min(
            unvisited,
            key=lambda idx: distance_func(nodes[current], nodes[idx])
        )
        
        # Ajouter la distance
        distance_to_nearest = distance_func(nodes[current], nodes[nearest_index])
        total_distance += distance_to_nearest
        
        # Aller au nœud le plus proche
        current = nearest_index
        route.append(current)
        unvisited.remove(current)
    
    # Retour à l'entrée (point de départ)
    distance_to_start = distance_func(nodes[current], nodes[start_index])
    total_distance += distance_to_start
    route.append(start_index)
    
    return route, total_distance


def calculate_route_distance(
    nodes: List[Location],
    route_indices: List[int],
    distance_func: Callable[[Location, Location], int] = manhattan
) -> int:
    """
    Calcule la distance totale d'un itinéraire donné.
    
    Args:
        nodes: Liste de tous les nœuds
        route_indices: Liste ordonnée des indices des nœuds à visiter
        distance_func: Fonction de calcul de distance
    
    Returns:
        Distance totale du parcours
    """
    total_distance = 0
    
    for i in range(len(route_indices) - 1):
        from_index = route_indices[i]
        to_index = route_indices[i + 1]
        total_distance += distance_func(nodes[from_index], nodes[to_index])
    
    return total_distance
