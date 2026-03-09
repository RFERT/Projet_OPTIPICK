from typing import Dict, List, Tuple, Any
from .models import Order, Product, Agent, Warehouse


class StorageOptimizer:
    """
    Analyse le stockage de l'entrepot pour proposer des ameliorations :
    - produits frequents pres de l'entree
    - produits souvent commandes ensemble proches les uns des autres
    """
    
    def __init__(self):
        pass
    
    def compute_product_frequency(self, orders: List[Order]) -> Dict[str, int]:
        """Compte combien de fois chaque produit a ete commande."""
        frequency = {}
        
        for order in orders:
            for item in order.items:
                product_id = item.product.id
                if product_id not in frequency:
                    frequency[product_id] = 0
                frequency[product_id] += item.quantity
        
        return frequency
    
    def compute_product_affinity(self, orders: List[Order]) -> Dict[Tuple[str, str], int]:
        """
        Calcule combien de fois deux produits sont commandes ensemble.
        Plus le chiffre est haut, plus ils devraient etre proches dans l'entrepot.
        """
        affinity = {}
        
        for order in orders:
            product_ids = [item.product.id for item in order.items]
            
            # toutes les paires de produits dans cette commande
            for i in range(len(product_ids)):
                for j in range(i + 1, len(product_ids)):
                    pid1, pid2 = product_ids[i], product_ids[j]
                    key = tuple(sorted([pid1, pid2]))
                    
                    if key not in affinity:
                        affinity[key] = 0
                    affinity[key] += 1
        
        return affinity
    
    def suggest_storage_reorganization(self, products: Dict[str, Product],
                                      orders: List[Order]) -> Dict[str, Any]:
        """
        Propose une reorganisation du stockage : les produits tres frequents
        vont pres de l'entree (zone A), les moyens au milieu, les rares au fond.
        """
        # calculer frequence
        frequency = self.compute_product_frequency(orders)
        
        # trier par frequence
        sorted_products = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        
        # creer les groupes par frequence
        n_products = len(sorted_products)
        high_freq = sorted_products[:int(n_products * 0.2)]      # top 20%
        medium_freq = sorted_products[int(n_products*0.2):int(n_products*0.6)]  # 20-60%
        low_freq = sorted_products[int(n_products*0.6):]          # 60%+
        
        return {
            'high_frequency_products': high_freq,
            'medium_frequency_products': medium_freq,
            'low_frequency_products': low_freq,
            'total_frequency': frequency,
        }