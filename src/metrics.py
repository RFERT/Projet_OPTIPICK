from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .models import Agent, Order, Product, Warehouse
from .utils import manhattan


@dataclass(frozen=True)
class OrderTotals:
    """Totaux d'une commande (poids + volume)."""
    weight: float
    volume: float


def compute_order_totals(order: Order, products: Dict[str, Product]) -> OrderTotals:
    """
    Calcule le poids et le volume total d'une commande.

    On parcourt les items de la commande :
    - on récupère le Product via son product_id
    - on ajoute (poids * quantité) et (volume * quantité)
    """
    total_w = 0.0
    total_v = 0.0

    for item in order.items:
        product = products[item.product_id]
        total_w += product.weight * item.quantity
        total_v += product.volume * item.quantity

    return OrderTotals(weight=total_w, volume=total_v)


def estimate_total_distance(
    orders: List[Order],
    products: Dict[str, Product],
    warehouse: Warehouse,
    round_trip: bool = False,
) -> int:
    """
    Distance totale estimée (Jour 1) :
    somme des distances Manhattan entre l'entrée et chaque produit de chaque commande.
    On multiplie par la quantité.

    round_trip=False : entrée -> produit (aller simple)
    round_trip=True  : entrée -> produit -> entrée (aller-retour, x2)
    """
    factor = 2 if round_trip else 1
    total = 0

    for order in orders:
        for item in order.items:
            product = products[item.product_id]
            total += manhattan(warehouse.entry_point, product.location) * item.quantity * factor

    return total


def compute_agent_usage(
    agents: List[Agent],
    assignments: Dict[str, List[str]],
    order_totals: Dict[str, Tuple[float, float]],
) -> Dict[str, Dict[str, float]]:
    """
    Utilisation par agent à partir du résultat d'allocation.

    - assignments: {agent_id: [order_id, ...]}
    - order_totals: {order_id: (weight, volume)} (déjà calculé pendant l'allocation)
    """
    usage: Dict[str, Dict[str, float]] = {}

    for agent in agents:
        order_ids = assignments.get(agent.id, [])
        total_w = 0.0
        total_v = 0.0

        for oid in order_ids:
            w, v = order_totals[oid]
            total_w += w
            total_v += v

        usage[agent.id] = {
            "orders": float(len(order_ids)),
            "weight": total_w,
            "volume": total_v,
        }

    return usage
