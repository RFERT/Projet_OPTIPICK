from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

from .models import *
from .utils import *
from .constraints import (
    check_capacity,
    check_incompatibilities,
    check_robot_restrictions,
    check_no_zones,
)


@dataclass
class AllocationResult:
    assignments: Dict[str, List[str]]
    unassigned: List[str]
    order_totals: Dict[str, Tuple[float, float]]
    cart_human: Dict[str, str]  # cart_id -> human_id
    routes: Dict[str, Dict] = field(default_factory=dict)  # agent_id -> {'route': [...], 'distance': ...}

# -------------------------------------------------
# JOUR 1 — allocation naïve
# -------------------------------------------------
def allocate_first_fit_day1(
    orders: List[Order],
    agents: List[Agent],
    products: Dict[str, Product],
) -> AllocationResult:
    assignments: Dict[str, List[str]] = {a.id: [] for a in agents}
    assignments: Dict[str, List[str]] = {a.id: [] for a in agents}
    unassigned: List[str] = []
    order_totals: Dict[str, Tuple[float, float]] = {}
    cart_human: Dict[str, str] = {}

    for order in orders:
        w, v = compute_order_totals(order, products)
        order_totals[order.id] = (w, v)

        placed = False
        for agent in agents:
            if w <= agent.capacity_weight and v <= agent.capacity_volume:
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


# -------------------------------------------------
# Distance estimée
# -------------------------------------------------
def estimate_total_distance(
    orders: List[Order],
    products: Dict[str, Product],
    warehouse: Warehouse,
    round_trip: bool = False,
) -> int:
    total = 0
    factor = 2 if round_trip else 1

    for order in orders:
        for it in order.items:
            p = products[it.product_id]
            total += manhattan(warehouse.entry_point, p.location) * it.quantity * factor

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



