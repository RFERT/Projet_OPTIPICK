from typing import Dict, Set, List, Tuple, Any
from .models import Agent, Order, Product, Location
import numpy as np


class AllocationOptimizer:
    """
    Optimise l'allocation des commandes : regroupement de commandes compatibles,
    equilibrage de la charge entre agents, etc.
    """
    
    def __init__(self):
        pass
    
    def compute_product_distance_sum(self, order: Order, products: Dict[str, Product]) -> float:
        """Somme des distances Manhattan de tous les produits d'une commande par rapport a l'entree."""
        entry_point = Location(0, 0)
        total_distance = 0.0
        
        for item in order.items:
            product = item.product
            if product:
                location = Location(product.location.x, product.location.y)
                distance = abs(location.x - entry_point.x) + abs(location.y - entry_point.y)
                total_distance += distance * item.quantity
        
        return total_distance
    
    def _can_combine_orders(self, order1: Order, order2: Order, 
                           products: Dict[str, Product]) -> bool:
        """Verifie si deux commandes peuvent etre combinees (pas de produits incompatibles)."""
        # checker les incompatibilites
        for item1 in order1.items:
            prod1 = item1.product
            if not prod1:
                continue
            
            for item2 in order2.items:
                prod2 = item2.product
                if not prod2:
                    continue
                
                # si les produits sont incompatibles
                if prod2.id in prod1.incompatible_with:
                    return False
        
        return True

    def find_compatible_orders(self, orders: List[Order], products: Dict[str, Product]) -> List[Set[str]]:
        """
        Trouve les paires de commandes qui peuvent etre regroupees
        (pas d'incompatibilites entre leurs produits).
        """
        compatible_groups = []
        
        # on teste toutes les paires
        for i in range(len(orders)):
            for j in range(i + 1, len(orders)):
                order1 = orders[i]
                order2 = orders[j]
                
                # verifier si les deux sont compatibles
                can_combine = self._can_combine_orders(order1, order2, products)
                
                if can_combine:
                    compatible_groups.append({order1.id, order2.id})
        
        return compatible_groups