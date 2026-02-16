from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .models import Agent, Order, Product, Warehouse
from .utils import manhattan


@dataclass
class AllocationResult:
    assignments: Dict[str, List[str]]          # agent_id -> [order_id...]
    unassigned: List[str]                      # order_id non placées
    order_totals: Dict[str, Tuple[float, float]]  # order_id -> (weight, volume)


def compute_order_totals(order: Order, products: Dict[str, Product]) -> Tuple[float, float]:
    """Calcule (poids_total, volume_total) de la commande."""
    total_w = 0.0
    total_v = 0.0
    for it in order.items:
        p = products[it.product_id]
        total_w += p.weight * it.quantity
        total_v += p.volume * it.quantity
    return total_w, total_v


def allocate_first_fit(
    orders: List[Order],
    agents: List[Agent],
    products: Dict[str, Product],
) -> AllocationResult:
    """
    Jour 1.4 : First-Fit
    - commandes dans l'ordre
    - assigner au 1er agent dont capacité (poids+volume) suffit
    - ignorer restrictions
    """
    assignments: Dict[str, List[str]] = {a.id: [] for a in agents}
    unassigned: List[str] = []
    order_totals: Dict[str, Tuple[float, float]] = {}

    for order in orders:  # ordre d'arrivée = ordre du fichier (jour 1)
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

    return AllocationResult(assignments=assignments, unassigned=unassigned, order_totals=order_totals)


def estimate_total_distance(orders: List[Order], products: Dict[str, Product], warehouse: Warehouse) -> int:
    """
    Jour 1.5 : Distance totale estimée = somme dist(entrée -> produit) * quantité
    (Ce n'est PAS une tournée optimisée; juste une estimation simple.)
    """
    total = 0
    for order in orders:
        for it in order.items:
            p = products[it.product_id]
            total += manhattan(warehouse.entry_point, p.location) * it.quantity
    return total
