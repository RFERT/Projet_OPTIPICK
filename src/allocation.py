from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import pdb
from itertools import cycle

from .models import *
from .utils import *
from .constraints import (check_capacity,
    check_incompatibilities,
    check_robot_restrictions,
    check_no_zones)


@dataclass
class AllocationResult:
    assignments: Dict[str, List[str]]
    unassigned: List[str]
    order_totals: Dict[str, Tuple[float, float]]
    cart_human: Dict[str, str]  # cart_id -> human_id
    routes: Dict[str, Dict] = field(default_factory=dict)  # agent_id -> {'route': [...], 'distance': ...}

def allocate_first_fit_day1(orders: List[Order], agents: List[Agent], products: Dict[str, Product]
                            ) -> AllocationResult:
    assignments: Dict[str, List[str]] = {a.id: [] for a in agents}
    unassigned: List[str] = []
    order_totals: Dict[str, Tuple[float, float]] = {}
    cart_human: Dict[str, str] = {}

    # Séparer les types d'agents
    robots = [a for a in agents if a.type == "robot"]
    humans = [a for a in agents if a.type == "human"]
    carts = [a for a in agents if a.type == "cart"]
    
    # Créer une rotation des agents pour équilibrer la charge
    robots_cycle = cycle(robots) if robots else None
    carts_cycle = cycle(carts) if carts else None
    humans_cycle = cycle(humans) if humans else None
    
    humans_used_with_cart: set = set()

    for order in orders:
        order_totals[order.id] = compute_order_totals(order, products)
        placed = False

        # 1. Essayer un robot (en rotation)
        if robots_cycle:
            for _ in range(len(robots)):  # Essayer chaque robot une fois
                agent = next(robots_cycle)
                if order_totals[order.id][0] <= agent.capacity_weight and order_totals[order.id][1] <= agent.capacity_volume:
                    assignments[agent.id].append(order.id)
                    placed = True
                    break
        
        if placed:
            continue
        
        # 2. Essayer chariot + humain (si commande trop lourde pour humain seul)
        if not placed and carts_cycle and (order_totals[order.id][0] > humans[0].capacity_weight if humans else False):
            for _ in range(len(carts)):
                cart = next(carts_cycle)
                for human in humans:
                    if human.id not in humans_used_with_cart:
                        if order_totals[order.id][0] <= cart.capacity_weight and order_totals[order.id][1] <= cart.capacity_volume:
                            assignments[cart.id].append(order.id)
                            assignments[human.id].append(order.id)
                            cart_human[cart.id] = human.id
                            humans_used_with_cart.add(human.id)
                            placed = True
                            break
                if placed:
                    break
        
        # 3. Essayer humain seul (en rotation)
        if not placed and humans_cycle:
            for _ in range(len(humans)):
                human = next(humans_cycle)
                if human.id not in humans_used_with_cart:
                    if order_totals[order.id][0] <= human.capacity_weight and order_totals[order.id][1] <= human.capacity_volume:
                        assignments[human.id].append(order.id)
                        placed = True
                        break

        if not placed:
            unassigned.append(order.id)

    return AllocationResult(
        assignments=assignments,
        unassigned=unassigned,
        order_totals=order_totals,
        cart_human=cart_human,
    )


# -------------------------------------------------
# JOUR 2 — allocation avec contraintes + cart nécessite humain
# -------------------------------------------------
def allocate_first_fit_day2(
    orders: List[Order],
    agents: List[Agent],
    products: Dict[str, Product],
    warehouse: Warehouse,
) -> AllocationResult:
    assignments: Dict[str, List[str]] = {a.id: [] for a in agents}
    unassigned: List[str] = []
    order_totals: Dict[str, Tuple[float, float]] = {}

    # humains disponibles pour accompagner les carts
    humans_available: List[str] = [a.id for a in agents if a.type == "human"]
    cart_human: Dict[str, str] = {}  # cart_id -> human_id
        # Tri automatique des agents pour Jour 2 : robot -> cart -> human
    type_priority = {"robot": 0, "cart": 1, "human": 2}
    agents_sorted = sorted(agents, key=lambda a: type_priority.get(a.type, 99))


    for order in orders:
        w, v = compute_order_totals(order, products)
        order_totals[order.id] = (w, v)

        placed = False
        for agent in agents_sorted:
            if not check_capacity(order, agent, products):
                continue
            if not check_incompatibilities(order, products):
                continue
            if not check_robot_restrictions(order, agent, products):
                continue
            if not check_no_zones(order, agent, products, warehouse):
                continue

            # règle cart → nécessite humain
            if agent.type == "cart":
                if agent.id not in cart_human:
                    # ce cart n'a pas encore d'humain assigné
                    if not humans_available:
                        continue
                    human_id = humans_available.pop(0)  # on réserve un humain
                    cart_human[agent.id] = human_id

            assignments[agent.id].append(order.id)
            placed = True
            break

        if not placed:
            unassigned.append(order.id)

    return AllocationResult(
        assignments=assignments,
        unassigned=unassigned,
        order_totals=order_totals,
        cart_human=cart_human,
    )


def estimate_total_distance(
    orders: List[Order],
    products: Dict[str, Product],
    warehouse: Warehouse
) -> int:
    total = 0
    for order in orders:
        for item in order.items:
            product = products[item.product.id]
            total += manhattan(warehouse.entry_point, product.location) * 2
            # print(f"DEBUG: {item.product.id} à {product.location}, distance={manhattan(warehouse.entry_point, product.location)}, qty={item.quantity} (produits égaux groupés)")

    return total


# -------------------------------------------------
# Optimisation TSP des itinéraires
# -------------------------------------------------
def optimize_allocation_routes(
    allocation_result: AllocationResult,
    orders: List[Order],
    products: Dict[str, Product],
    warehouse: Warehouse,
) -> AllocationResult:
    """
    Ajoute les itinéraires optimisés (TSP) aux résultats d'allocation.
    
    Args:
        allocation_result: Résultats d'allocation (assignments)
        orders: Liste de toutes les commandes
        products: Dictionnaire des produits
        warehouse: Entrepôt (pour le point d'entrée)
    
    Returns:
        AllocationResult enrichi avec les routes optimisées
    """
    from .routing import optimize_team_routes
    
    # Créer un dictionnaire des commandes
    orders_dict = {o.id: o for o in orders}
    
    # Optimiser les routes pour chaque agent
    routes = optimize_team_routes(
        allocation_result.assignments,
        orders,
        products,
        warehouse.entry_point
    )
    
    # Ajouter les routes au résultat
    allocation_result.routes = routes
    
    return allocation_result