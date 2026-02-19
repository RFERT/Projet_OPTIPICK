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

def extract_unique_locations(products: List[Product]) -> Set[Location]:
    """
    Extrait tous les emplacements uniques des produits.
    
    Args:
        products: Liste des produits
    
    Returns:
        Ensemble des emplacements uniques
    """
    unique_locations = set()
    
    for product in products:
        unique_locations.add(product.location)
    
    return unique_locations


def build_nodes_with_entry(entry_point: Location, unique_locations: Set[Location]) -> List[Location]:
    """
    Construit la liste des nœuds avec entrée au début et à la fin.
    
    Args:
        entry_point: Point d'entrée de l'entrepôt
        unique_locations: Ensemble des emplacements à visiter
    
    Returns:
        Liste : [Entrée] + [Produits] + [Entrée]
    """
    locations_list = list(unique_locations)
    
    # Circuit fermé : [Entrée] + [Produits] + [Entrée]
    nodes = [entry_point] + locations_list + [entry_point]
    
    return nodes


def compute_distance_matrix(nodes: List[Location]) -> List[List[int]]:
    """
    Calcule la matrice des distances Manhattan entre tous les nœuds.
    
    Args:
        nodes: Liste des nœuds (locations)
    
    Returns:
        Matrice carrée des distances
    """
    n = len(nodes)
    distance_matrix = [[0] * n for _ in range(n)]
    
    # Pour chaque nœud de départ
    for node_from_index in range(n):
        # Calculer les distances vers les nœuds suivants (optimisation)
        for node_to_index in range(node_from_index, n):
            distance = manhattan(nodes[node_from_index], nodes[node_to_index])
            
            # Remplir à la fois [from][to] et [to][from] (symétrie)
            distance_matrix[node_from_index][node_to_index] = distance
            distance_matrix[node_to_index][node_from_index] = distance
    
    return distance_matrix

