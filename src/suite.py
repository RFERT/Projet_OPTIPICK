"""
OPTIPICK - Jours 3, 4 et 5
═══════════════════════════════════════════════════════════════════════════════
Jour 3 : Optimisation des tournées (TSP)
Jour 4 : Allocation optimale et regroupement (CSP)
Jour 5 : Optimisation du stockage et analyse avancée
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import numpy as np
import pandas as pd
from itertools import permutations, combinations
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from .models import Agent, Order, Product, Warehouse, Location


# ═══════════════════════════════════════════════════════════════════════════════
# JOUR 3 : OPTIMISATION DES TOURNÉES (TSP - Traveling Salesman Problem)
# ═══════════════════════════════════════════════════════════════════════════════

class TSPOptimizer:
    """
    Résout le problème du voyageur de commerce (TSP) pour chaque agent.
    
    Objectif : Trouver l'ordre optimal de visite des emplacements pour minimiser
    la distance totale parcourue.
    
    Étapes :
    1. Extraire les emplacements uniques pour chaque agent
    2. Calculer la matrice de distances
    3. Résoudre TSP avec heuristique Nearest Neighbor
    4. Optionnel : Améliorer avec 2-opt
    """
    
    def __init__(self, warehouse: Warehouse):
        """
        Initialise l'optimiseur TSP.
        
        Args:
            warehouse: L'entrepôt (contient entry_point et grille)
        """
        self.warehouse = warehouse
        self.entry_point = Location(warehouse.entry_point.x, warehouse.entry_point.y)
    
    def extract_locations(self, agent_assignments: Dict[str, List[str]], 
                         orders: List[Order], products: Dict[str, Product]) -> Dict[str, Set[Location]]:
        """
        Extrait tous les emplacements uniques à visiter pour chaque agent.
        
        Exemple :
        - Agent R1 a commandes [Order_001, Order_002]
        - Order_001 contient Product_A (zone (1,1)), Product_B (zone (2,1))
        - Order_002 contient Product_C (zone (1,2))
        - Locations de R1 = {(1,1), (2,1), (1,2)}
        
        Args:
            agent_assignments: Dict[agent_id] = List[order_id]
            orders: Liste des commandes
            products: Dict[product_id] = Product
            
        Returns:
            Dict[agent_id] = Set[Location]
        """
        locations_per_agent = {}
        
        for agent_id, order_ids in agent_assignments.items():
            locations = set()
            
            for order_id in order_ids:
                # Trouver la commande
                order = next((o for o in orders if o.id == order_id), None)
                if not order:
                    continue
                
                # Pour chaque produit dans la commande
                for item in order.items:
                    product = item.product
                    if product:
                        location = Location(product.location.x, product.location.y)
                        locations.add(location)
            
            locations_per_agent[agent_id] = locations
        
        return locations_per_agent
    
    def compute_distance_matrix(self, locations: List[Location]) -> np.ndarray:
        """
        Calcule la matrice de distances (Manhattan) entre tous les emplacements.
        
        La matrice est carrée : distance[i][j] = distance de location_i à location_j
        
        Args:
            locations: Liste des emplacements
            
        Returns:
            Matrice de distances (numpy array)
        """
        n = len(locations)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Distance de Manhattan : |x1 - x2| + |y1 - y2|
                    matrix[i][j] = abs(locations[i].x - locations[j].x) + \
                                  abs(locations[i].y - locations[j].y)
        
        return matrix
    
    def nearest_neighbor_tsp(self, locations: List[Location]) -> List[int]:
        """
        Résout TSP avec l'heuristique Nearest Neighbor (plus proche voisin).
        
        Algorithme :
        1. Commencer à l'entrée (index 0)
        2. À chaque étape, aller au plus proche voisin non visité
        3. Retourner à l'entrée
        
        Complexité : O(n²)
        Qualité : Généralement 85-95% de l'optimal
        
        Args:
            locations: Liste des emplacements
            
        Returns:
            Liste des indices dans l'ordre de visite
        """
        n = len(locations)
        if n <= 1:
            return list(range(n))
        
        # Calculer matrice de distances
        distances = self.compute_distance_matrix(locations)
        
        # Commencer à l'entrée (on la place en index 0)
        visited = [False] * n
        route = [0]  # Commencer à l'entrée
        visited[0] = True
        current = 0
        
        # Visiter les n-1 autres emplacements
        for _ in range(n - 1):
            # Trouver le plus proche non visité
            nearest = -1
            min_distance = float('inf')
            
            for j in range(n):
                if not visited[j] and distances[current][j] < min_distance:
                    nearest = j
                    min_distance = distances[current][j]
            
            if nearest != -1:
                route.append(nearest)
                visited[nearest] = True
                current = nearest
        
        return route
    
    def optimize_agent_route(self, agent: Agent, locations: List[Location]) -> Tuple[List[Location], float]:
        """
        Optimise la tournée d'un agent spécifique.
        
        Args:
            agent: L'agent
            locations: Emplacements à visiter
            
        Returns:
            (route optimisée, distance totale)
        """
        if not locations:
            return [], 0.0
        
        # Ajouter l'entrée comme première location (point de départ/retour)
        all_locations = [self.entry_point] + list(locations)
        
        # Résoudre TSP
        route_indices = self.nearest_neighbor_tsp(all_locations)
        
        # Construire la route et calculer la distance
        route = [all_locations[i] for i in route_indices]
        distance = self._calculate_route_distance(route)
        
        # Calculer le temps total
        time_minutes = (distance / agent.speed) * 60  # Temps en minutes
        
        return route, distance, time_minutes
    
    def _calculate_route_distance(self, route: List[Location]) -> float:
        """
        Calcule la distance totale d'une route.
        
        Args:
            route: Liste des emplacements dans l'ordre
            
        Returns:
            Distance totale
        """
        total_distance = 0.0
        for i in range(len(route) - 1):
            loc1 = route[i]
            loc2 = route[i + 1]
            total_distance += abs(loc1.x - loc2.x) + abs(loc1.y - loc2.y)
        
        # Retour à l'entrée
        if route:
            last_loc = route[-1]
            entry = self.entry_point
            total_distance += abs(last_loc.x - entry.x) + abs(last_loc.y - entry.y)
        
        return total_distance


def run_day3(assignments: Dict[str, List[str]], agents: List[Agent], 
             orders: List[Order], products: Dict[str, Product], 
             warehouse: Warehouse) -> Dict:
    """
    JOUR 3 : Optimisation des tournées avec TSP.
    
    Résumé :
    --------
    À partir de l'allocation du Jour 2, on optimise l'ordre de visite des
    emplacements pour chaque agent afin de minimiser la distance parcourue.
    
    Résultats attendus :
    - Distance optimisée (par rapport au Jour 1-2)
    - Temps de tournée pour chaque agent
    - Nouvelles routes détaillées
    
    Args:
        assignments: Allocation commandes → agents
        agents: Liste des agents
        orders: Liste des commandes
        products: Dict des produits
        warehouse: L'entrepôt
        
    Returns:
        Dict avec résultats du Jour 3
    """
    print("\n" + "="*80)
    print("JOUR 3 : OPTIMISATION DES TOURNÉES (TSP)")
    print("="*80)
    
    optimizer = TSPOptimizer(warehouse)
    
    # 1. Extraire les emplacements par agent
    print("\n[1/3] Extraction des emplacements à visiter...")
    locations_per_agent = optimizer.extract_locations(assignments, orders, products)
    
    # 2. Optimiser les tournées
    print("\n[2/3] Optimisation des tournées avec Nearest Neighbor...")
    optimized_routes = {}
    total_distance_optimized = 0.0
    total_time = 0.0
    
    for agent in agents:
        if agent.id not in assignments or not assignments[agent.id]:
            continue
        
        locations = list(locations_per_agent.get(agent.id, set()))
        if not locations:
            continue
        
        route, distance, time_minutes = optimizer.optimize_agent_route(agent, locations)
        optimized_routes[agent.id] = {
            'route': route,
            'distance': distance,
            'time_minutes': time_minutes,
            'locations_count': len(locations)
        }
        
        total_distance_optimized += distance
        total_time += time_minutes
        
        print(f"  {agent.id} : {len(locations)} emplacements, "
              f"distance={distance:.2f}m, temps={time_minutes:.1f}min")
    
    # 3. Résumé et comparaison
    print("\n[3/3] Résumé des résultats...")
    print(f"\n  Distance totale optimisée : {total_distance_optimized:.2f}m")
    print(f"  Temps total : {total_time:.1f} minutes ({total_time/60:.1f}h)")
    
    results_day3 = {
        'optimized_routes': optimized_routes,
        'total_distance': total_distance_optimized,
        'total_time_minutes': total_time,
        'locations_per_agent': {k: len(v) for k, v in locations_per_agent.items()}
    }
    
    return results_day3


# ═══════════════════════════════════════════════════════════════════════════════
# JOUR 4 : ALLOCATION OPTIMALE ET REGROUPEMENT (CSP - Constraint Satisfaction)
# ═══════════════════════════════════════════════════════════════════════════════

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


def run_day4(assignments: Dict[str, List[str]], agents: List[Agent],
             orders: List[Order], products: Dict[str, Product]) -> Dict:
    """
    JOUR 4 : Allocation optimale et regroupement.
    
    Résumé :
    --------
    On améliore l'allocation du Jour 2 en :
    1. Regroupant les commandes compatibles
    2. Ré-optimisant l'allocation pour minimiser le coût global
    3. Vérifiant l'équilibre de charge entre agents
    
    Résultats attendus :
    - Groupes de commandes optimisés
    - Nouvelle allocation améliorée
    - Métriques comparatives
    
    Args:
        assignments: Allocation actuelle (Jour 2)
        agents: Liste des agents
        orders: Liste des commandes
        products: Dict des produits
        
    Returns:
        Dict avec résultats du Jour 4
    """
    print("\n" + "="*80)
    print("JOUR 4 : ALLOCATION OPTIMALE ET REGROUPEMENT (CSP)")
    print("="*80)
    
    optimizer = AllocationOptimizer()
    
    # 1. Analyser les ordres compatibles
    print("\n[1/2] Analyse des groupes de commandes compatibles...")
    compatible_groups = optimizer.find_compatible_orders(orders, products)
    print(f"  {len(compatible_groups)} groupes de commandes compatibles trouvés")
    
    # 2. Calculer les métriques de balance
    print("\n[2/2] Analyse d'équilibre de charge...")
    
    agent_loads = {}
    for agent in agents:
        if agent.id in assignments:
            agent_loads[agent.id] = len(assignments[agent.id])
    
    avg_load = np.mean(list(agent_loads.values())) if agent_loads else 0
    std_load = np.std(list(agent_loads.values())) if agent_loads else 0
    
    print(f"  Charge moyenne par agent : {avg_load:.1f} commandes")
    print(f"  Écart-type : {std_load:.2f} (plus bas = mieux)")
    
    # Détail par agent
    for agent_id, load in agent_loads.items():
        print(f"    {agent_id} : {load} commandes")
    
    results_day4 = {
        'compatible_groups': compatible_groups,
        'agent_loads': agent_loads,
        'avg_load': avg_load,
        'std_load': std_load
    }
    
    return results_day4


# ═══════════════════════════════════════════════════════════════════════════════
# JOUR 5 : OPTIMISATION DU STOCKAGE ET ANALYSE AVANCÉE
# ═══════════════════════════════════════════════════════════════════════════════

class StorageOptimizer:
    """
    Analyse et optimise le stockage dans l'entrepôt.
    
    Objectifs :
    1. Identifier les produits fréquemment commandés → placer près de l'entrée
    2. Grouper produits souvent co-commandés → placer proches
    3. Réorganiser pour minimiser les distances futures
    """
    
    def __init__(self):
        pass
    
    def compute_product_frequency(self, orders: List[Order]) -> Dict[str, int]:
        """
        Compte le nombre de fois que chaque produit est commandé.
        
        Args:
            orders: Liste des commandes
            
        Returns:
            Dict[product_id] = nombre de fois commandé
        """
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
        Calcule l'affinité entre paires de produits
        (nombre de fois commandés ensemble).
        
        Args:
            orders: Liste des commandes
            
        Returns:
            Dict[(product_id_1, product_id_2)] = nombre de fois ensemble
        """
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
                                      orders: List[Order]) -> Dict[str, any]:
        """
        Propose une réorganisation du stockage.
        
        Stratégie :
        1. Produits très fréquents → Zone A (proche entrée)
        2. Produits moyens → Zone B, C
        3. Produits rares → Zone D, E (loin)
        
        Args:
            products: Dict des produits
            orders: Liste des commandes
            
        Returns:
            Dict avec suggestions de réorganisation
        """
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


def run_day5(orders: List[Order], products: Dict[str, Product], 
             agents: List[Agent], warehouse: Warehouse) -> Dict:
    """
    JOUR 5 : Optimisation du stockage et analyse avancée.
    
    Résumé :
    --------
    On analyse les patterns de commandes pour proposer une réorganisation
    optimale du stockage et fournir des recommandations pour le futur.
    
    Étapes :
    1. Analyser la fréquence de chaque produit
    2. Identifier les affinités (produits souvent achetés ensemble)
    3. Proposer une nouvelle organisation spatiale
    4. Générer recommandations
    
    Résultats attendus :
    - Propositions de réorganisation
    - Analyse des patterns
    - Estimations d'amélioration
    
    Args:
        orders: Liste des commandes
        products: Dict des produits
        agents: Liste des agents
        warehouse: L'entrepôt
        
    Returns:
        Dict avec résultats du Jour 5
    """
    print("\n" + "="*80)
    print("JOUR 5 : OPTIMISATION DU STOCKAGE ET ANALYSE AVANCÉE")
    print("="*80)
    
    optimizer = StorageOptimizer()
    
    # 1. Analyser les patterns
    print("\n[1/3] Analyse des patterns de commandes...")
    frequency = optimizer.compute_product_frequency(orders)
    affinity = optimizer.compute_product_affinity(orders)
    
    print(f"  {len(frequency)} produits différents commandés")
    print(f"  {len(affinity)} paires de produits souvent achetées ensemble")
    
    # Produits les plus commandés
    top_products = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n  Top 5 produits les plus commandés :")
    for pid, count in top_products:
        product = products.get(pid)
        if product:
            print(f"    - {product.name} : {count} fois")
    
    # 2. Proposer réorganisation
    print("\n[2/3] Proposition de réorganisation du stockage...")
    reorganization = optimizer.suggest_storage_reorganization(products, orders)
    
    print(f"  Produits haute fréquence (à rapprocher de l'entrée) : "
          f"{len(reorganization['high_frequency_products'])}")
    print(f"  Produits moyenne fréquence : "
          f"{len(reorganization['medium_frequency_products'])}")
    print(f"  Produits basse fréquence (éloigner) : "
          f"{len(reorganization['low_frequency_products'])}")
    
    # 3. Recommandations
    print("\n[3/3] Recommandations...")
    
    # Recommandation 1 : Robots vs Humains
    print("\n  RECOMMANDATION 1 : Utilisation des agents")
    print("    - Les robots gèrent les produits légers et accumulables")
    print("    - Les humains gèrent les produits fragiles")
    print("    - Chariots : réserver pour gros volumes (surtout alimentaire)")
    
    # Recommandation 2 : Zones
    print("\n  RECOMMANDATION 2 : Organisation des zones")
    print("    - Zone A (près entrée) : Produits très fréquents (électronique rapide)")
    print("    - Zone B (mid) : Produits moyens (livres, textiles)")
    print("    - Zone C (frigo) : Alimentaire - accès humain prioritaire")
    print("    - Zone D (loin) : Chimie - accès humain exclusif")
    print("    - Zone E (extensible) : Réserve et surplus")
    
    # Recommandation 3 : Améliorations futures
    print("\n  RECOMMANDATION 3 : Investissements recommandés")
    print("    - +1 robot high-speed pour commandes express")
    print("    - Système d'étagères dynamiques (comme Kiva robots)")
    print("    - Capteurs de stock en temps réel")
    
    results_day5 = {
        'product_frequency': frequency,
        'product_affinity': affinity,
        'reorganization_proposal': reorganization,
        'recommendations': {
            'agent_strategy': 'Robots pour léger, Humains pour fragile/complexe',
            'zone_strategy': 'Zone A = fréquent, Zone E = rare',
            'future_investments': ['Extra robot', 'Dynamic shelves', 'Real-time inventory']
        }
    }
    
    return results_day5


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION : Exécuter les 3 jours
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_days_suite(assignments: Dict[str, List[str]], agents: List[Agent],
                       orders: List[Order], products: Dict[str, Product],
                       warehouse: Warehouse) -> Dict:
    """
    Exécute les Jours 3, 4 et 5 en séquence.
    
    Args:
        assignments: Allocation du Jour 2
        agents: Liste des agents
        orders: Liste des commandes
        products: Dict des produits
        warehouse: L'entrepôt
        
    Returns:
        Dict avec tous les résultats
    """
    results = {}
    
    # Jour 3
    results['day3'] = run_day3(assignments, agents, orders, products, warehouse)
    
    # Jour 4
    results['day4'] = run_day4(assignments, agents, orders, products)
    
    # Jour 5
    results['day5'] = run_day5(orders, products, agents, warehouse)
    
    return results