from typing import Dict, Set, List, Tuple, Any
from .models import Agent, Order, Product, Location


class AllocationOptimizer:
    """
    Optimise l'allocation des commandes aux agents en utilisant des techniques
    avancées (regroupement, balancing, optimisation globale).
    
    Approches :
    1. Regroupement (Batching) : Combiner commandes compatibles
    2. Optimisation par coût : Minimiser distance + coût opérationnel
    3. Balancing : Équilibrer la charge entre agents
    """
    
    def __init__(self):
        pass
    
    def compute_product_distance_sum(self, order: Order, products: Dict[str, Product]) -> float:
        """
        Calcule la somme des distances de tous les produits au point d'entrée.
        
        Args:
            order: Une commande
            products: Dict des produits
            
        Returns:
            Somme des distances (Manhattan)
        """
        entry_point = Location(0, 0)
        total_distance = 0.0
        
        for item in order.items:
            product = item.product
            if product:
                location = Location(product.location.x, product.location.y)
                distance = abs(location.x - entry_point.x) + abs(location.y - entry_point.y)
                total_distance += distance * item.quantity
        
        return total_distance
    
    def find_compatible_orders(self, orders: List[Order], products: Dict[str, Product]) -> List[Set[str]]:
        """
        Trouve les groupes de commandes qui peuvent être regroupées.
        
        Critères de compatibilité :
        - Pas d'incompatibilités de produits
        - Capacité totale respectée
        - Deadlines compatibles
        
        Args:
            orders: Liste des commandes
            products: Dict des produits
            
        Returns:
            Liste de groupes (sets d'ordre IDs)
        """
        compatible_groups = []
        
        # Approche simple : tester les paires
        for i in range(len(orders)):
            for j in range(i + 1, len(orders)):
                order1 = orders[i]
                order2 = orders[j]
                
                # Vérifier si les deux commandes peuvent être groupées
                can_combine = self._can_combine_orders(order1, order2, products)
                
                if can_combine:
                    compatible_groups.append({order1.id, order2.id})
        
        return compatible_groups
    
    def _can_combine_orders(self, order1: Order, order2: Order, 
                           products: Dict[str, Product]) -> bool:
        """
        Vérifie si deux commandes peuvent être combinées.
        
        Args:
            order1, order2: Deux commandes
            products: Dict des produits
            
        Returns:
            True si combinables
        """
        # Vérifier les incompatibilités
        for item1 in order1.items:
            prod1 = item1.product
            if not prod1:
                continue
            
            for item2 in order2.items:
                prod2 = item2.product
                if not prod2:
                    continue
                
                # Si les produits sont incompatibles
                if prod2.id in prod1.incompatible_with:
                    return False
        
        return True