from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
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


def split_agents_by_type(agents: List[Agent]):
    """Separe les agents en 3 listes : robots, humans, carts."""
    robots = [a for a in agents if a.type == "robot"]
    humans = [a for a in agents if a.type == "human"]
    carts = [a for a in agents if a.type == "cart"]
    return robots, humans, carts


def try_robot_day1(order_id, weight, volume, robots, robots_cycle, assignments):
    """Essaie d'assigner la commande a un robot en rotation."""
    if not robots_cycle:
        return False
    for _ in range(len(robots)):
        agent = next(robots_cycle)
        if weight <= agent.capacity_weight and volume <= agent.capacity_volume:
            assignments[agent.id].append(order_id)
            return True
    return False


def try_cart_human_day1(order_id, weight, volume, carts, carts_cycle, humans,
                        assignments, cart_human, humans_used_with_cart):
    """Essaie d'assigner la commande a un chariot + humain (jour 1)."""
    if not carts_cycle:
        return False
    # on tente que si c'est trop lourd pour un humain seul
    if humans and weight <= humans[0].capacity_weight:
        return False
    for _ in range(len(carts)):
        cart = next(carts_cycle)
        for human in humans:
            if human.id not in humans_used_with_cart:
                if weight <= cart.capacity_weight and volume <= cart.capacity_volume:
                    assignments[cart.id].append(order_id)
                    assignments[human.id].append(order_id)
                    cart_human[cart.id] = human.id
                    humans_used_with_cart.add(human.id)
                    return True
    return False


def try_human_day1(order_id, weight, volume, humans, humans_cycle, assignments, humans_used_with_cart):
    """Essaie d'assigner la commande a un humain seul (jour 1)."""
    if not humans_cycle:
        return False
    for _ in range(len(humans)):
        human = next(humans_cycle)
        if human.id not in humans_used_with_cart:
            if weight <= human.capacity_weight and volume <= human.capacity_volume:
                assignments[human.id].append(order_id)
                return True
    return False


def allocate_first_fit_day1(orders: List[Order], agents: List[Agent], products: Dict[str, Product]
                            ) -> AllocationResult:
    assignments: Dict[str, List[str]] = {a.id: [] for a in agents}
    unassigned: List[str] = []
    order_totals: Dict[str, Tuple[float, float]] = {}
    cart_human: Dict[str, str] = {}

    robots, humans, carts = split_agents_by_type(agents)

    # rotation pour equilibrer la charge
    robots_cycle = cycle(robots) if robots else None
    carts_cycle = cycle(carts) if carts else None
    humans_cycle = cycle(humans) if humans else None

    humans_used_with_cart: set = set()

    for order in orders:
        w, v = compute_order_totals(order, products)
        order_totals[order.id] = (w, v)

        placed = try_robot_day1(order.id, w, v, robots, robots_cycle, assignments)

        if not placed:
            placed = try_cart_human_day1(order.id, w, v, carts, carts_cycle, humans,
                                         assignments, cart_human, humans_used_with_cart)

        if not placed:
            placed = try_human_day1(order.id, w, v, humans, humans_cycle,
                                    assignments, humans_used_with_cart)

        if not placed:
            unassigned.append(order.id)

    return AllocationResult(
        assignments=assignments,
        unassigned=unassigned,
        order_totals=order_totals,
        cart_human=cart_human,
    )


def pair_carts_with_humans(carts, humans):
    """Associe chaque chariot a un humain (autant que possible)."""
    cart_human = {}
    for i, cart in enumerate(carts):
        if i < len(humans):
            cart_human[cart.id] = humans[i].id
    return cart_human


def try_robot_day2(order, robots, assignments, products, warehouse):
    """Essaie d'assigner la commande au robot le moins charge, avec contraintes."""
    if not robots:
        return False
    best_robot = min(robots, key=lambda a: len(assignments[a.id]))
    if (check_capacity(order, best_robot, products) and
        check_incompatibilities(order, products) and
        check_robot_restrictions(order, best_robot, products) and
        check_no_zones(order, best_robot, products, warehouse)):
        assignments[best_robot.id].append(order.id)
        return True
    return False


def try_cart_human_day2(order, carts, cart_human, assignments, products, warehouse):
    """Essaie d'assigner la commande a un chariot + humain, avec contraintes."""
    if not carts:
        return False
    carts_with_humans = sorted(
        [(cart, cart_human[cart.id]) for cart in carts if cart.id in cart_human],
        key=lambda x: len(assignments[x[0].id]))
    for cart, human_id in carts_with_humans:
        if (check_capacity(order, cart, products) and
            check_incompatibilities(order, products) and
            check_robot_restrictions(order, cart, products) and
            check_no_zones(order, cart, products, warehouse)):
            assignments[cart.id].append(order.id)
            assignments[human_id].append(order.id)
            return True
    return False


def try_human_day2(order, humans, human_used_with_cart, assignments, products, warehouse):
    """Essaie d'assigner la commande a un humain libre, avec contraintes."""
    if not humans:
        return False
    free_humans = [h for h in humans if h.id not in human_used_with_cart]
    if not free_humans:
        return False
    best_human = min(free_humans, key=lambda a: len(assignments[a.id]))
    if (check_capacity(order, best_human, products) and
        check_incompatibilities(order, products) and
        check_robot_restrictions(order, best_human, products) and
        check_no_zones(order, best_human, products, warehouse)):
        assignments[best_human.id].append(order.id)
        return True
    return False


def allocate_first_fit_day2(orders: List[Order], agents: List[Agent], products: Dict[str, Product], warehouse: Warehouse) -> AllocationResult:
    assignments: Dict[str, List[str]] = {a.id: [] for a in agents}
    unassigned: List[str] = []
    order_totals: Dict[str, Tuple[float, float]] = {}

    robots, humans, carts = split_agents_by_type(agents)
    cart_human = pair_carts_with_humans(carts, humans)
    human_used_with_cart: set = set(cart_human.values())

    for order in orders:
        w, v = compute_order_totals(order, products)
        order_totals[order.id] = (w, v)
        placed = False

        if not placed:
            placed = try_robot_day2(order, robots, assignments, products, warehouse)
        if not placed:
            placed = try_cart_human_day2(order, carts, cart_human, assignments, products, warehouse)
        if not placed:
            placed = try_human_day2(order, humans, human_used_with_cart, assignments, products, warehouse)
        if not placed:
            unassigned.append(order.id)

    return AllocationResult(
        assignments=assignments,
        unassigned=unassigned,
        order_totals=order_totals,
        cart_human=cart_human)


def estimate_total_distance(orders: List[Order], products: Dict[str, Product], warehouse: Warehouse) -> int:
    total = 0
    for order in orders:
        for item in order.items:
            product = products[item.product.id]
            total += manhattan(warehouse.entry_point, product.location) * 2
            # print(f"DEBUG: {item.product.id} à {product.location}, distance={manhattan(warehouse.entry_point, product.location)}, qty={item.quantity} (produits égaux groupés)")

    return total


def optimize_allocation_routes(
    allocation_result: AllocationResult,
    orders: List[Order],
    products: Dict[str, Product],
    warehouse: Warehouse,
) -> AllocationResult:
    """Ajoute les routes optimisees (TSP) aux resultats d'allocation."""
    from .routing import optimize_team_routes
    
    orders_dict = {o.id: o for o in orders}
    
    # optimiser les routes pour chaque agent
    routes = optimize_team_routes(
        allocation_result.assignments,
        orders,
        products,
        warehouse.entry_point
    )
    
    # ajouter les routes au resultat
    allocation_result.routes = routes
    
    return allocation_result