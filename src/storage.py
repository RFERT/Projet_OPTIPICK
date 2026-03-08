from typing import Dict, List, Tuple, Any
from .models import Order, Product


class StorageOptimizer:
    def __init__(self):
        pass
    
    def compute_product_frequency(self, orders: List[Order]) -> Dict[str, int]:
        frequency = {}
        
        for order in orders:
            for item in order.items:
                product_id = item.product.id
                if product_id not in frequency:
                    frequency[product_id] = 0
                frequency[product_id] += item.quantity
        
        return frequency
    
    def compute_product_affinity(self, orders: List[Order]) -> Dict[Tuple[str, str], int]:
        affinity = {}
        
        for order in orders:
            product_ids = [item.product.id for item in order.items]
            
            # Toutes les paires de produits dans cette commande
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

        # Calculer fréquence
        frequency = self.compute_product_frequency(orders)
        
        # Trier par fréquence
        sorted_products = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        
        # Créer zones de densité
        n_products = len(sorted_products)
        high_freq = sorted_products[:int(n_products * 0.2)]      # Top 20%
        medium_freq = sorted_products[int(n_products*0.2):int(n_products*0.6)]  # 20-60%
        low_freq = sorted_products[int(n_products*0.6):]          # 60%+
        
        return {
            'high_frequency_products': high_freq,
            'medium_frequency_products': medium_freq,
            'low_frequency_products': low_freq,
            'total_frequency': frequency,
        }
