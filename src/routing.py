<<<<<<< HEAD
"""
Jour 3 - Objectif: Optimiser l'ordre de visite des emplacements pour chaque agent
"""

from typing import List, Set, Tuple, Callable
from src.models import Product, Location, Agent
from src.utils import manhattan

=======
from typing import List, Tuple, Callable, Set
from .models import Location, Product, Order
from .utils import manhattan

def nearest_neighbor_tsp(
    locations: List[Location],
    start: Location,
    distance_func: Callable[[Location, Location], float] = manhattan
) -> List[Location]:
    """
    Résout le TSP avec l'heuristique du Plus Proche Voisin (Nearest Neighbor).
    
    Args:
        locations: Liste des emplacements à visiter
        start: Point de départ (entrée de l'entrepôt)
        distance_func: Fonction de calcul de distance (défaut: Manhattan)
    
    Returns:
        Liste ordonnée des emplacements à visiter (incluant le retour à start)
    
    Algorithme:
        1. Commencer au point de départ
        2. À chaque étape, aller à l'emplacement non visité le plus proche
        3. Répéter jusqu'à visiter tous les emplacements
        4. Retourner au point de départ
    """
    if not locations:
        return [start]
    
    # Copie pour ne pas modifier la liste originale
    unvisited = set(locations)
    route = [start]
    current = start
    
    # Visiter tous les emplacements
    while unvisited:
        # Trouver l'emplacement non visité le plus proche
        nearest = min(unvisited, key=lambda loc: distance_func(current, loc))
        route.append(nearest)
        current = nearest
        unvisited.remove(nearest)
    
    # Retourner à l'entrée
    route.append(start)
    
    return route


def calculate_route_distance(
    route: List[Location],
    distance_func: Callable[[Location, Location], float] = manhattan
) -> float:
    """
    Calcule la distance totale d'un itinéraire.
    
    Args:
        route: Liste ordonnée des emplacements
        distance_func: Fonction de calcul de distance
    
    Returns:
        Distance totale du parcours
    """
    total_distance = 0.0
    for i in range(len(route) - 1):
        total_distance += distance_func(route[i], route[i + 1])
    return total_distance


def optimize_agent_route(
    assigned_orders: List[Order],
    products: dict,
    warehouse_entry: Location,
    distance_func: Callable[[Location, Location], float] = manhattan
) -> Tuple[List[Location], float]:
    """
    Optimise l'itinéraire d'un agent pour ses commandes assignées.
    
    Args:
        assigned_orders: Commandes assignées à l'agent
        products: Dictionnaire des produits {product_id: Product}
        warehouse_entry: Point d'entrée de l'entrepôt
        distance_func: Fonction de calcul de distance
    
    Returns:
        Tuple (itinéraire optimisé, distance totale)
    """
    # Extraire tous les emplacements uniques des produits dans les commandes
    locations = set()
    for order in assigned_orders:
        for item in order.items:
            product = products[item.product_id]
            locations.add(product.location)
    
    # Résoudre le TSP
    locations_list = list(locations)
    route = nearest_neighbor_tsp(locations_list, warehouse_entry, distance_func)
    distance = calculate_route_distance(route, distance_func)
    
    return route, distance


def optimize_team_routes(
    assignments: dict,
    orders: List[Order],
    products: dict,
    warehouse_entry: Location,
    distance_func: Callable[[Location, Location], float] = manhattan
) -> dict:
    """
    Optimise les itinéraires pour tous les agents d'une équipe.
    
    Args:
        assignments: Dict {agent_id: [order_ids]}
        orders: Liste de toutes les commandes
        products: Dictionnaire des produits
        warehouse_entry: Point d'entrée
        distance_func: Fonction de calcul de distance
    
    Returns:
        Dict {agent_id: {'route': [locations], 'distance': float}}
    """
    orders_dict = {o.id: o for o in orders}
    routes = {}
    
    for agent_id, order_ids in assignments.items():
        if not order_ids:
            routes[agent_id] = {'route': [warehouse_entry, warehouse_entry], 'distance': 0.0}
        else:
            assigned_orders = [orders_dict[oid] for oid in order_ids]
            route, distance = optimize_agent_route(
                assigned_orders,
                products,
                warehouse_entry,
                distance_func
            )
            routes[agent_id] = {'route': route, 'distance': distance}
    
    return routes


# ========== Fonctions Jour 3 - Complémentaires ==========
>>>>>>> 96c01d84ce00169fba1988dc5d4a0b12baecd67b

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
