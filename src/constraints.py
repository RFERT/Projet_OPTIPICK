from typing import Dict, List
from .models import Product, Agent, Order




def check_capacity(order: Order, agent: Agent, products: Dict[str, Product]) -> bool:
   
    total_weight = 0.0
    total_volume = 0.0

    # Parcourir chaque article (OrderItem) de la commande
    for order_item in order.items:
        product = order_item.product
        
        total_weight += product.weight * order_item.quantity
        
        total_volume += product.volume * order_item.quantity

    # Vérifier les deux contraintes:
    can_fit_weight = total_weight <= agent.capacity_weight
    can_fit_volume = total_volume <= agent.capacity_volume
    
    return can_fit_weight and can_fit_volume


def can_combine(order_items: List) -> bool:
  
    # Convertir OrderItems en liste de Products
    products = [item.product for item in order_items]
    
    if len(products) <= 1:
        return True
    
    # Parcourir toutes les PAIRES de produits
    for index_i in range(len(products)):
        for index_j in range(index_i + 1, len(products)):
            product_i = products[index_i]
            product_j = products[index_j]
            
            # Vérifier l'incompatibilité DANS LES DEUX DIRECTIONS
            if product_j.id in product_i.incompatible_with:
                return False 
            
            if product_i.id in product_j.incompatible_with:
                return False 
    
    return True


def check_incompatibilities(order: Order, products: Dict[str, Product]) -> bool:
    return can_combine(order.items)


def check_robot_restrictions(order: Order, agent: Agent, products: Dict[str, Product]) -> bool:
    # Les humains et les chariots peuvent tout livrer (pas de restrictions)
    if agent.type != "robot":
        return True
    
    # Récupérer les restrictions du robot
    restrictions = agent.restrictions
    
    # Récupérer les limites spécifiques du robot
    has_no_fragile_restriction = restrictions.get("no_fragile", False)
    max_item_weight = restrictions.get("max_item_weight", float('inf'))
    
    # Vérifier chaque produit de la commande par rapport aux restrictions du robot
    for order_item in order.items:
        product = order_item.product
        
        if has_no_fragile_restriction and product.fragile:
            return False
        
        if product.weight > max_item_weight:
            return False
    
    # Aucune restriction violée
    return True


def check_no_zones(order: Order, agent: Agent, products: Dict[str, Product], warehouse) -> bool:
    # Récupérer les zones interdites pour cet agent
    no_zones = agent.restrictions.get("no_zones", [])
    
    if not no_zones:
        return True
    
    # Vérifier que AUCUN produit n'est dans une zone interdite
    for order_item in order.items:
        product = order_item.product
        
        zone = get_zone_of_location(warehouse, product.location)
        
        if zone and zone in no_zones:
            return False
    
    return True


def get_zone_of_location(warehouse, location) -> str | None:

    if not warehouse or not hasattr(warehouse, 'zones'):
        return None
    
    for zone_code, zone_info in warehouse.zones.items():
        coords = zone_info.get("coords", [])
        # Vérifier si [location.x, location.y] est dans cette zone
        if [location.x, location.y] in coords:
            return zone_code
    
    return None


def is_human_available_for_cart(human_id: str, used_with_carts: set) -> bool:
    return human_id not in used_with_carts


def get_available_human_for_cart(humans: List[Agent], used_with_carts: set) -> Agent | None:
    
    for human in humans:
        if is_human_available_for_cart(human.id, used_with_carts):
            return human
    
    # Aucun humain disponible
    return None


def can_pair_cart_human(cart: Agent, human: Agent, order: Order, products: Dict[str, Product]) -> bool:
    # Vérifier capacité du chariot
    if not check_capacity(order, cart, products):
        return False
    
    # Vérifier incompatibilités
    if not check_incompatibilities(order, products):
        return False
    
    return True