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


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE TSPOptimizer - Optimisation avancée des tournées
# ═══════════════════════════════════════════════════════════════════════════════

import numpy as np
from .models import Agent, Order, Product, Warehouse

class TSPOptimizer:
    """
    Résout le problème du voyageur de commerce (TSP) pour chaque agent.
    
    Objectif : Trouver l'ordre optimal de visite des emplacements pour minimiser
    la distance totale parcourue.
    
    Étapes :
    1. Extraire les emplacements uniques pour chaque agent
    2. Calculer la matrice de distances
    3. Résoudre TSP avec heuristique Nearest Neighbor
    4. Optionnel : Améliorer avec 2-opt
    """
    
    def __init__(self, warehouse: Warehouse):
        """
        Initialise l'optimiseur TSP.
        
        Args:
            warehouse: L'entrepôt (contient entry_point et grille)
        """
        self.warehouse = warehouse
        self.entry_point = Location(warehouse.entry_point.x, warehouse.entry_point.y)
    
    def extract_locations(self, agent_assignments: dict, 
                         orders: List[Order], products: dict) -> dict:
        """
        Extrait tous les emplacements uniques à visiter pour chaque agent.
        
        Exemple :
        - Agent R1 a commandes [Order_001, Order_002]
        - Order_001 contient Product_A (zone (1,1)), Product_B (zone (2,1))
        - Order_002 contient Product_C (zone (1,2))
        - Locations de R1 = {(1,1), (2,1), (1,2)}
        
        Args:
            agent_assignments: Dict[agent_id] = List[order_id]
            orders: Liste des commandes
            products: Dict[product_id] = Product
            
        Returns:
            Dict[agent_id] = Set[Location]
        """
        locations_per_agent = {}
        
        for agent_id, order_ids in agent_assignments.items():
            locations = set()
            
            for order_id in order_ids:
                # Trouver la commande
                order = next((o for o in orders if o.id == order_id), None)
                if not order:
                    continue
                
                # Pour chaque produit dans la commande
                for item in order.items:
                    product = item.product
                    if product:
                        location = Location(product.location.x, product.location.y)
                        locations.add(location)
            
            locations_per_agent[agent_id] = locations
        
        return locations_per_agent
    
    def compute_distance_matrix(self, locations: List[Location]) -> np.ndarray:
        """
        Calcule la matrice de distances (Manhattan) entre tous les emplacements.
        
        La matrice est carrée : distance[i][j] = distance de location_i à location_j
        
        Args:
            locations: Liste des emplacements
            
        Returns:
            Matrice de distances (numpy array)
        """
        n = len(locations)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Distance de Manhattan : |x1 - x2| + |y1 - y2|
                    matrix[i][j] = abs(locations[i].x - locations[j].x) + \
                                  abs(locations[i].y - locations[j].y)
        
        return matrix
    
    def nearest_neighbor_tsp(self, locations: List[Location]) -> List[int]:
        """
        Résout TSP avec l'heuristique Nearest Neighbor (plus proche voisin).
        
        Algorithme :
        1. Commencer à l'entrée (index 0)
        2. À chaque étape, aller au plus proche voisin non visité
        3. Retourner à l'entrée
        
        Complexité : O(n²)
        Qualité : Généralement 85-95% de l'optimal
        
        Args:
            locations: Liste des emplacements
            
        Returns:
            Liste des indices dans l'ordre de visite
        """
        n = len(locations)
        if n <= 1:
            return list(range(n))
        
        # Calculer matrice de distances
        distances = self.compute_distance_matrix(locations)
        
        # Commencer à l'entrée (on la place en index 0)
        visited = [False] * n
        route = [0]  # Commencer à l'entrée
        visited[0] = True
        current = 0
        
        # Visiter les n-1 autres emplacements
        for _ in range(n - 1):
            # Trouver le plus proche non visité
            nearest = -1
            min_distance = float('inf')
            
            for j in range(n):
                if not visited[j] and distances[current][j] < min_distance:
                    nearest = j
                    min_distance = distances[current][j]
            
            if nearest != -1:
                route.append(nearest)
                visited[nearest] = True
                current = nearest
        
        return route
    
    def optimize_agent_route(self, agent: Agent, locations: List[Location]) -> Tuple[List[Location], float, float]:
        """
        Optimise la tournée d'un agent spécifique.
        
        Args:
            agent: L'agent
            locations: Emplacements à visiter
            
        Returns:
            (route optimisée, distance totale, temps en minutes)
        """
        if not locations:
            return [], 0.0, 0.0
        
        # Ajouter l'entrée comme première location (point de départ/retour)
        all_locations = [self.entry_point] + list(locations)
        
        # Résoudre TSP
        route_indices = self.nearest_neighbor_tsp(all_locations)
        
        # Construire la route et calculer la distance
        route = [all_locations[i] for i in route_indices]
        distance = self._calculate_route_distance(route)
        
        # Calculer le temps total
        time_minutes = (distance / agent.speed) * 60  # Temps en minutes
        
        return route, distance, time_minutes
    
    def _calculate_route_distance(self, route: List[Location]) -> float:
        """
        Calcule la distance totale d'une route.
        
        Args:
            route: Liste des emplacements dans l'ordre
            
        Returns:
            Distance totale
        """
        total_distance = 0.0
        for i in range(len(route) - 1):
            loc1 = route[i]
            loc2 = route[i + 1]
            total_distance += abs(loc1.x - loc2.x) + abs(loc1.y - loc2.y)
        
        # Retour à l'entrée
        if route:
            last_loc = route[-1]
            entry = self.entry_point
            total_distance += abs(last_loc.x - entry.x) + abs(last_loc.y - entry.y)
        
        return total_distance
