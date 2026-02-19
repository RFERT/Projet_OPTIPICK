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
