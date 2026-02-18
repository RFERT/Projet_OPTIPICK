from typing import Dict, List
from .models import Product, Agent, Order


def check_capacity(order: Order, agent: Agent, products: Dict[str, Product]) -> bool:
    total_w = 0
    total_v = 0

    for it in order.items:
        p = products[it.product_id]
        total_w += p.weight * it.quantity
        total_v += p.volume * it.quantity

    return total_w <= agent.capacity_weight and total_v <= agent.capacity_volume


def check_incompatibilities(order: Order, products: Dict[str, Product]) -> bool:
    seen = set()

    for it in order.items:
        p = products[it.product_id]

        for other in seen:
            if p.id in products[other].incompatible_with:
                return False

        seen.add(p.id)

    return True


def check_robot_restrictions(order: Order, agent: Agent, products: Dict[str, Product]) -> bool:
    if agent.type != "robot":
        return True

    for it in order.items:
        p = products[it.product_id]

        if p.fragile:
            return False

        if p.weight > 10:
            return False

    return True

def explain_rejection(order: Order, agent: Agent, products: Dict[str, Product]) -> str:
    if not check_capacity(order, agent, products):
        return "capacité insuffisante (poids/volume)"
    if not check_incompatibilities(order, products):
        return "produits incompatibles dans la commande"
    if not check_robot_restrictions(order, agent, products):
        return "restriction robot (fragile ou item trop lourd)"
    return "OK"


def get_zone_of_location(warehouse, loc) -> str | None:
    """
    Retourne la zone (ex: "A","B","C"...) pour une Location.
    On cherche dans warehouse.zones[zone]["coords"] qui contient des [x,y].
    """
    for zone_code, zone_info in warehouse.zones.items():
        coords = zone_info.get("coords", [])
        if [loc.x, loc.y] in coords:
            return zone_code
    return None


def check_no_zones(order: Order, agent: Agent, products: Dict[str, Product], warehouse) -> bool:
    """
    Vérifie que l'agent n'entre pas dans les zones interdites (restriction 'no_zones').
    Si pas de restriction, OK.
    """
    no_zones = agent.restrictions.get("no_zones", [])
    if not no_zones:
        return True

    for it in order.items:
        p = products[it.product_id]
        z = get_zone_of_location(warehouse, p.location)
        if z is not None and z in no_zones:
            return False

    return True

