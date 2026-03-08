from typing import List, Tuple, Callable, Set
from .models import Location, Product, Order
from .utils import manhattan

def nearest_neighbor_tsp(
    locations: List[Location],
    start: Location,
    distance_func: Callable[[Location, Location], float] = manhattan
) -> List[Location]:
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
    unique_locations = set()
    
    for product in products:
        unique_locations.add(product.location)
    
    return unique_locations


def build_nodes_with_entry(entry_point: Location, unique_locations: Set[Location]) -> List[Location]:
    locations_list = list(unique_locations)  # Convertir SET en LISTE
    
    # Circuit fermé : [Entrée] + [Produits] + [Entrée]
    nodes = [entry_point] + locations_list + [entry_point]
    
    return nodes


def compute_distance_matrix(nodes: List[Location]) -> List[List[int]]:
    n = len(nodes)
    distance_matrix = [[0] * n for _ in range(n)]
    
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


def nearest_neighbor_tsp(
    nodes: List[Location],
    start_index: int = 0,
    distance_func: Callable[[Location, Location], int] = manhattan
) -> Tuple[List[int], int]:
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
    total_distance = 0
    
    for i in range(len(route_indices) - 1):
        from_index = route_indices[i]
        to_index = route_indices[i + 1]
        total_distance += distance_func(nodes[from_index], nodes[to_index])
    
    return total_distance


import numpy as np
from .models import Agent, Order, Product, Warehouse

class TSPOptimizer:
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.entry_point = Location(warehouse.entry_point.x, warehouse.entry_point.y)
    
    def extract_locations(self, agent_assignments: dict, 
                         orders: List[Order], products: dict) -> dict:
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
        n = len(locations)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = abs(locations[i].x - locations[j].x) + \
                                  abs(locations[i].y - locations[j].y)
        
        return matrix
    
    def nearest_neighbor_tsp(self, locations: List[Location]) -> List[int]:
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
