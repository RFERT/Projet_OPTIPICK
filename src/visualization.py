import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import time
from collections import deque
from typing import Dict, List, Tuple, Set

from .models import Warehouse, Product, Agent, Order, Location
from .utils import manhattan


ZONE_COLORS = {
    'A': '#FF6B6B',      # Electronique
    'B': '#4ECDC4',      # Livres
    'C': '#45B7D1',      # Alimentaire
    'D': '#F7DC6F',      # Chimie
    'E': '#BB8FCE',      # Textile
    '0': '#EEEEEE'       # Allee
}

AGENT_COLORS = {
    'R1': '#FF6B6B', 'R2': '#FF8E72', 'R3': '#FFA500',
    'C1': '#4ECDC4', 'C2': '#45B7D1',
    'H1': '#96CEB4', 'H2': '#BBDC9E'
}

AGENT_COLORS_ROUTE = {
    'R1': 'blue', 'R2': 'darkblue', 'R3': 'lightblue',
    'H1': 'green', 'H2': 'darkgreen',
    'C1': 'orange', 'C2': 'darkorange'
}


def build_walkable_set(warehouse):
    """Construit l'ensemble des cases praticables (allees + emplacements produits + entree)."""
    walkable = set()
    for y in range(warehouse.height):
        for x in range(warehouse.width):
            cell = warehouse.grid[y][x]
            # les allees ('0'), l'entree ('1'), et les zones produit (A-E) sont praticables
            if cell != '':
                walkable.add((x, y))
    return walkable


def bfs_path(start: Location, end: Location, walkable: set) -> List[Location]:
    """
    Trouve le chemin le plus court entre deux cases praticables via BFS.
    Se deplace case par case (haut, bas, gauche, droite uniquement).
    """
    if start == end:
        return [start]
    
    start_tuple = (start.x, start.y)
    end_tuple = (end.x, end.y)
    
    if start_tuple not in walkable or end_tuple not in walkable:
        # fallback : chemin direct si une case n'est pas praticable
        return [start, end]
    
    queue = deque([(start_tuple, [start_tuple])])
    visited = {start_tuple}
    
    while queue:
        (cx, cy), path = queue.popleft()
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) == end_tuple:
                full_path = path + [(nx, ny)]
                return [Location(x, y) for x, y in full_path]
            if (nx, ny) in walkable and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
    
    # pas de chemin trouve -> fallback direct
    return [start, end]


def expand_route_through_aisles(waypoints: List[Location], walkable: set) -> List[Location]:
    """
    Transforme une liste de waypoints (entree -> produits -> entree) en route
    complete case par case en passant par les allees via BFS.
    """
    if len(waypoints) < 2:
        return waypoints
    
    full_route = [waypoints[0]]
    for i in range(len(waypoints) - 1):
        segment = bfs_path(waypoints[i], waypoints[i + 1], walkable)
        # on saute le premier point du segment car c'est deja le dernier de full_route
        full_route.extend(segment[1:])
    
    return full_route


def draw_grid_cells(ax, grid):
    """Dessine chaque case de la grille avec sa couleur de zone."""
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            cell = grid[y][x]
            color = ZONE_COLORS.get(cell, '#FFFFFF')
            rect = patches.Rectangle((x-0.5, y-0.5), 1, 1, 
                                    linewidth=1, edgecolor='black', 
                                    facecolor=color, alpha=0.6)
            ax.add_patch(rect)
            if cell != '0':
                ax.text(x, y, cell, ha='center', va='center', 
                       fontsize=10, fontweight='bold', color='white')


def draw_highlighted_locations(ax, highlight_locations):
    """Surligne certains emplacements sur le plan (petits cercles rouges)."""
    if not highlight_locations:
        return
    for loc in highlight_locations:
        circle = plt.Circle((loc.x, loc.y), 0.15, color='red', alpha=0.8, zorder=5)
        ax.add_patch(circle)


def draw_agent_markers(ax, agent_positions):
    """Affiche les agents sur le plan avec leur marqueur specifique."""
    if not agent_positions:
        return
    for agent_id, (x, y) in agent_positions.items():
        color = AGENT_COLORS_ROUTE.get(agent_id, 'gray')
        marker = '*' if 'R' in agent_id else ('s' if 'H' in agent_id else '^')
        ax.plot(x, y, marker=marker, markersize=15, color=color, 
               label=agent_id, zorder=10)


def draw_entry_point(ax, warehouse):
    """Dessine le point d'entree de l'entrepot."""
    entry_x, entry_y = warehouse.entry_point.x, warehouse.entry_point.y
    ax.plot(entry_x, entry_y, marker='X', markersize=20, color='gold', 
           label='Entree', zorder=10, markeredgecolor='black', markeredgewidth=2)


def setup_warehouse_axes(ax, grid, title):
    """Configure les axes pour un plan d'entrepot."""
    ax.set_xlim(-1, len(grid[0]))
    ax.set_ylim(-1, len(grid))
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.set_xlabel('X (colonne)', fontsize=10)
    ax.set_ylabel('Y (ligne)', fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3, linestyle='--')


def draw_warehouse_grid(warehouse: Warehouse, products: Dict[str, Product],
                        agent_positions: Dict[str, Tuple[int, int]] = None,
                        highlight_locations: Set[Location] = None,
                        title: str = "Plan d'Entrepot") -> plt.Figure:
    """Dessine le plan de l'entrepot avec les zones, les produits et eventuellement les agents."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    grid = warehouse.grid
    draw_grid_cells(ax, grid)
    draw_highlighted_locations(ax, highlight_locations)
    draw_agent_markers(ax, agent_positions)
    draw_entry_point(ax, warehouse)
    setup_warehouse_axes(ax, grid, title)
    
    plt.tight_layout()
    return fig


def draw_agent_route(warehouse: Warehouse, route: List[Location], 
                    agent_id: str, title: str = "Route d'agent") -> plt.Figure:
    """Dessine la route d'un agent sur le plan de l'entrepot."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # grille de fond
    grid = warehouse.grid
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            rect = patches.Rectangle((x-0.5, y-0.5), 1, 1,
                                    linewidth=0.5, edgecolor='gray',
                                    facecolor='white', alpha=0.3)
            ax.add_patch(rect)
    
    # tracer la route
    if route:
        x_coords = [loc.x for loc in route]
        y_coords = [loc.y for loc in route]
        
        ax.plot(x_coords, y_coords, 'b-', linewidth=2, alpha=0.6, label='Trajet')
        ax.plot(x_coords, y_coords, 'bo', markersize=8, alpha=0.6)
        
        # numero de chaque etape
        for i, (x, y) in enumerate(zip(x_coords, y_coords)):
            ax.text(x + 0.15, y + 0.15, str(i), fontsize=8, 
                   bbox=dict(boxstyle='circle', facecolor='yellow', alpha=0.7))
    
    # entree
    entry_x, entry_y = warehouse.entry_point.x, warehouse.entry_point.y
    ax.plot(entry_x, entry_y, marker='X', markersize=20, color='gold', label='Entree')
    
    ax.set_xlim(-1, len(grid[0]))
    ax.set_ylim(-1, len(grid))
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.set_title(f"{title} - {agent_id}", fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def collect_agent_route_locations(order_ids, orders_dict, warehouse):
    """Recupere les emplacements pour un agent (entree -> produits -> entree)."""
    locations = [Location(warehouse.entry_point.x, warehouse.entry_point.y)]
    for order_id in order_ids:
        order = orders_dict.get(order_id)
        if order:
            for item in order.items:
                product = item.product
                if product:
                    locations.append(Location(product.location.x, product.location.y))
    locations.append(Location(warehouse.entry_point.x, warehouse.entry_point.y))
    return locations


def simulate_agent_movements_data(warehouse: Warehouse, products: Dict[str, Product],
                                  assignments: Dict[str, List[str]], orders: List[Order],
                                  agents: List[Agent],
                                  cart_human: Dict[str, str] = None) -> Tuple[Dict[str, List[Location]], Dict[str, 'Agent']]:
    """
    Prepare les donnees de simulation (routes des agents).
    Les routes passent par les allees (BFS case par case).
    Les chariots suivent la meme route que leur humain associe (via cart_human).
    """
    agent_dict = {a.id: a for a in agents}
    orders_dict = {o.id: o for o in orders}
    if cart_human is None:
        cart_human = {}
    
    walkable = build_walkable_set(warehouse)
    
    agent_routes = {}
    for agent_id, order_ids in assignments.items():
        if not order_ids:
            agent_routes[agent_id] = [Location(warehouse.entry_point.x, warehouse.entry_point.y)]
        else:
            waypoints = collect_agent_route_locations(order_ids, orders_dict, warehouse)
            agent_routes[agent_id] = expand_route_through_aisles(waypoints, walkable)
    
    # les chariots doivent suivre exactement la route de leur humain
    for cart_id, human_id in cart_human.items():
        if human_id in agent_routes and len(agent_routes[human_id]) > 1:
            agent_routes[cart_id] = list(agent_routes[human_id])
    
    return agent_routes, agent_dict


def compute_agent_position_at_progress(route: List[Location], progress_ratio: float) -> Location:
    """
    Calcule la position d'un agent sur sa route case par case.
    La route est deja expandue en pas de 1 case, on prend simplement
    l'index correspondant au ratio de progression.
    """
    if not route:
        return Location(0, 0)
    if len(route) < 2:
        return route[0]
    
    # clamp entre 0 et 1
    progress_ratio = max(0.0, min(1.0, progress_ratio))
    
    # index dans la route (la route est case par case)
    index = int(progress_ratio * (len(route) - 1))
    index = min(index, len(route) - 1)
    
    return route[index]


def build_zone_grid(warehouse):
    """Construit la grille numpy des zones pour l'affichage imshow."""
    grid_height = warehouse.height
    grid_width = warehouse.width
    grid = np.zeros((grid_height, grid_width))
    
    zone_colors_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
    for zone_id, zone_data in warehouse.zones.items():
        zone_value = zone_colors_map.get(zone_id, 1)
        if isinstance(zone_data, dict) and 'coords' in zone_data:
            for x, y in zone_data['coords']:
                if 0 <= y < grid_height and 0 <= x < grid_width:
                    grid[y, x] = zone_value
    return grid, grid_width, grid_height


def draw_product_dots(ax, products):
    """Dessine les produits en petits points gris."""
    for product in products.values():
        ax.plot(product.location.x, product.location.y, 'o', 
               color='gray', markersize=8, alpha=0.5)


def draw_agent_routes_background(ax, agent_routes):
    """Dessine les trajets des agents en fond (pointilles)."""
    for agent_id, route in agent_routes.items():
        color = AGENT_COLORS.get(agent_id, '#999999')
        for i in range(len(route) - 1):
            ax.plot([route[i].x, route[i+1].x], 
                   [route[i].y, route[i+1].y],
                   color=color, linewidth=1, alpha=0.3, linestyle='--')


def draw_agent_current_positions(ax, agent_positions, agent_dict):
    """Dessine la position actuelle de chaque agent avec son marqueur."""
    for agent_id, pos in agent_positions.items():
        agent = agent_dict.get(agent_id)
        marker = 'D' if agent and agent.type == 'robot' else 's' if agent and agent.type == 'cart' else 'P'
        color = AGENT_COLORS.get(agent_id, '#999999')
        ax.plot(pos.x, pos.y, marker=marker, markersize=15, color=color,
               label=agent_id, zorder=10, markeredgecolor='black', markeredgewidth=2)


def draw_simulation_frame(warehouse: Warehouse, products: Dict[str, Product],
                          agent_routes: Dict[str, List[Location]],
                          agent_positions: Dict[str, Location],
                          agent_dict: Dict[str, Agent],
                          progress_ratio: float) -> plt.Figure:
    """Dessine une frame de la simulation avec les agents, leurs routes et les zones."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    grid, grid_width, grid_height = build_zone_grid(warehouse)
    ax.imshow(grid, cmap='Pastel1', alpha=0.5, extent=[0, grid_width, grid_height, 0])
    
    draw_product_dots(ax, products)
    draw_agent_routes_background(ax, agent_routes)
    draw_agent_current_positions(ax, agent_positions, agent_dict)
    draw_entry_point(ax, warehouse)
    
    ax.set_xlim(-1, grid_width)
    ax.set_ylim(-1, grid_height)
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(f"Simulation Temps Reel - Progression: {progress_ratio*100:.1f}%")
    ax.legend(loc='upper right', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
