from typing import List, Tuple, Callable, Set, Dict
from .models import Location, Product, Order
from .utils import manhattan


def extract_unique_locations(products: List[Product]) -> Set[Location]:
    unique_locations = set()
    
    for product in products:
        unique_locations.add(product.location)
    
    return unique_locations


def build_nodes_with_entry(entry_point: Location, unique_locations: Set[Location]) -> List[Location]:
    locations_list = list(unique_locations)
    
    # circuit ferme : entree -> produits -> entree
    nodes = [entry_point] + locations_list + [entry_point]
    
    return nodes


def compute_distance_matrix(nodes: List[Location]) -> List[List[int]]:
    """Matrice des distances Manhattan entre tous les noeuds."""
    n = len(nodes)
    distance_matrix = [[0] * n for _ in range(n)]
    
    for node_from_index in range(n):
        # on remplit que la moitie (symetrie) pour aller plus vite
        for node_to_index in range(node_from_index, n):
            distance = manhattan(nodes[node_from_index], nodes[node_to_index])
            
            # on remplit les deux cotes de la matrice
            distance_matrix[node_from_index][node_to_index] = distance
            distance_matrix[node_to_index][node_from_index] = distance
    
    return distance_matrix


def nearest_neighbor_tsp(
    nodes: List[Location],
    start_index: int = 0,
    distance_func: Callable[[Location, Location], int] = manhattan
) -> Tuple[List[int], int]:
    """
    Resout le TSP en allant toujours au noeud non visite le plus proche.
    C'est pas optimal mais ca donne un bon resultat en O(n^2).
    """
    n = len(nodes)
    unvisited = set(range(n))
    current = start_index
    route = [current]
    unvisited.remove(current)
    total_distance = 0
    
    # visiter tous les noeuds un par un
    while unvisited:
        # trouver le noeud non visite le plus proche
        nearest_index = min(
            unvisited,
            key=lambda idx: distance_func(nodes[current], nodes[idx])
        )
        
        # ajouter la distance
        distance_to_nearest = distance_func(nodes[current], nodes[nearest_index])
        total_distance += distance_to_nearest
        
        # se deplacer vers ce noeud
        current = nearest_index
        route.append(current)
        unvisited.remove(current)
    
    # retour au depart
    distance_to_start = distance_func(nodes[current], nodes[start_index])
    total_distance += distance_to_start
    route.append(start_index)
    
    return route, total_distance


def calculate_route_distance(
    nodes: List[Location],
    route_indices: List[int],
    distance_func: Callable[[Location, Location], int] = manhattan
) -> int:
    """Calcule la distance totale d'un trajet donne par ses indices."""
    total_distance = 0
    
    for i in range(len(route_indices) - 1):
        from_index = route_indices[i]
        to_index = route_indices[i + 1]
        total_distance += distance_func(nodes[from_index], nodes[to_index])
    
    return total_distance


def optimize_agent_route(
    assigned_orders: List[Order],
    products: dict,
    warehouse_entry: Location,
    distance_func: Callable[[Location, Location], float] = manhattan
) -> Tuple[List[Location], float]:
    """
    Optimise le trajet d'un agent en recuperant tous les emplacements de ses commandes
    puis en resolvant le TSP dessus.
    """
    # on recupere tous les emplacements uniques des produits a aller chercher
    locations = set()
    for order in assigned_orders:
        for item in order.items:
            product = products[item.product_id]
            locations.add(product.location)
    
    # resoudre le TSP
    locations_list = list(locations)
    nodes = [warehouse_entry] + locations_list + [warehouse_entry]
    route_indices, total_distance = nearest_neighbor_tsp(nodes, 0, distance_func)
    route = [nodes[i] for i in route_indices]
    
    return route, total_distance


def optimize_team_routes(
    assignments: dict,
    orders: List[Order],
    products: dict,
    warehouse_entry: Location,
    distance_func: Callable[[Location, Location], float] = manhattan
) -> dict:
    """Optimise les routes de tous les agents. Chacun a ses commandes, on calcule le meilleur trajet."""
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


import numpy as np
from .models import Agent, Order, Product, Warehouse

class TSPOptimizer:
    """
    Classe qui resout le TSP pour chaque agent.
    On extrait les emplacements, on calcule les distances, et on optimise avec nearest neighbor.
    """
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.entry_point = Location(warehouse.entry_point.x, warehouse.entry_point.y)

    def get_order_locations(self, order: Order, products: dict) -> Set[Location]:
        """Recupere les emplacements uniques des produits d'une commande."""
        locations = set()
        for item in order.items:
            product = item.product
            if product:
                locations.add(Location(product.location.x, product.location.y))
        return locations
    
    def compute_distance_matrix(self, locations: List[Location]) -> np.ndarray:
        """Matrice de distances Manhattan entre tous les emplacements."""
        n = len(locations)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                d = abs(locations[i].x - locations[j].x) + abs(locations[i].y - locations[j].y)
                matrix[i][j] = d
                matrix[j][i] = d
        
        return matrix
    
    def find_nearest_unvisited(self, distances, current, visited):
        """Trouve le noeud non visite le plus proche du noeud courant."""
        nearest = -1
        min_distance = float('inf')
        for j in range(len(visited)):
            if not visited[j] and distances[current][j] < min_distance:
                nearest = j
                min_distance = distances[current][j]
        return nearest
    
    def _calculate_route_distance(self, route: List[Location]) -> float:
        """Calcule la distance totale d'une route + retour a l'entree."""
        total_distance = 0.0
        for i in range(len(route) - 1):
            loc1 = route[i]
            loc2 = route[i + 1]
            total_distance += abs(loc1.x - loc2.x) + abs(loc1.y - loc2.y)
        
        # retour a l'entree
        if route:
            last_loc = route[-1]
            entry = self.entry_point
            total_distance += abs(last_loc.x - entry.x) + abs(last_loc.y - entry.y)
        
        return total_distance

    def build_optimized_route(self, all_locations, route_indices):
        """Construit la route (liste de Location) a partir des indices TSP."""
        return [all_locations[i] for i in route_indices]

    def extract_locations(self, agent_assignments: dict, 
                         orders: List[Order], products: dict) -> dict:
        """
        Pour chaque agent, on recupere tous les emplacements uniques des produits
        de ses commandes. Ca nous donne les points a visiter pour le TSP.
        """
        locations_per_agent = {}
        orders_dict = {o.id: o for o in orders}
        
        for agent_id, order_ids in agent_assignments.items():
            locations = set()
            for order_id in order_ids:
                order = orders_dict.get(order_id)
                if not order:
                    continue
                locations.update(self.get_order_locations(order, products))
            locations_per_agent[agent_id] = locations
        
        return locations_per_agent
    
    def nearest_neighbor_tsp(self, locations: List[Location]) -> List[int]:
        """
        Nearest Neighbor pour le TSP : on part de l'entree (index 0), 
        et on va toujours au plus proche non visite. C'est en O(n^2) et ca donne un bon resultat.
        """
        n = len(locations)
        if n <= 1:
            return list(range(n))
        
        distances = self.compute_distance_matrix(locations)
        
        visited = [False] * n
        route = [0]
        visited[0] = True
        current = 0
        
        for _ in range(n - 1):
            nearest = self.find_nearest_unvisited(distances, current, visited)
            if nearest != -1:
                route.append(nearest)
                visited[nearest] = True
                current = nearest
        
        return route
    
    def optimize_agent_route(self, agent: Agent, locations: List[Location]) -> Tuple[List[Location], float, float]:
        """Optimise la tournee d'un agent : on fait le TSP sur ses emplacements et on calcule le temps."""
        if not locations:
            return [], 0.0, 0.0
        
        all_locations = [self.entry_point] + list(locations)
        route_indices = self.nearest_neighbor_tsp(all_locations)
        route = self.build_optimized_route(all_locations, route_indices)
        distance = self._calculate_route_distance(route)
        time_minutes = (distance / agent.speed) * 60
        
        return route, distance, time_minutes
