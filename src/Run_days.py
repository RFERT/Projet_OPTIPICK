from src.loader import Warehouse, Product, Agent, Order
from src.allocation import allocate_first_fit_day1, allocate_first_fit_day2, estimate_total_distance
from src.routing import TSPOptimizer
from src.optimization import AllocationOptimizer
from typing import Dict, List
from src.utils import compute_order_totals
from src.storage import StorageOptimizer
import numpy as np


def print_assignments(agents, assignments):
    """Affiche l'allocation de chaque agent."""
    for agent in agents:
        agent_orders = assignments[agent.id]
        print(f"- {agent.id} ({agent.type}): {len(agent_orders)} commande(s) -> {agent_orders}")


def print_agent_utilization(agents, assignments, order_totals):
    """Affiche l'utilisation (poids/volume) par agent."""
    print("\nUtilisation par agent (poids/volume total des commandes assignees) :")
    for agent in agents:
        total_w = 0.0
        total_v = 0.0
        for order_id in assignments[agent.id]:
            w, v = order_totals[order_id]
            total_w += w
            total_v += v
        print(
            f"- {agent.id}: nb_commandes={len(assignments[agent.id])} | "
            f"poids={total_w:.2f}/{agent.capacity_weight} | "
            f"volume={total_v:.2f}/{agent.capacity_volume}"
        )


def print_day1_evaluation(orders, agents, result, products, warehouse):
    """Affiche les metriques d'evaluation du jour 1."""
    dist_one_way = estimate_total_distance(orders, products, warehouse)
    assigned_count = sum(len(lst) for lst in result.assignments.values())

    print("\nEvaluation Jour 1")
    print(f"Nombre de commandes assignees : {assigned_count}/{len(orders)}")
    print(f"Distance estimee (Allers retours pour chaque produit) : {dist_one_way}")


def print_day1_detailed_utilization(agents, result):
    """Affiche l'utilisation detaillee du jour 1 (avec max par commande)."""
    print("\nUtilisation par agent (poids/volume total des commandes assignees) :")
    for agent in agents:
        total_w = 0.0
        total_v = 0.0
        max_w = 0.0
        max_v = 0.0
        for order_id in result.assignments[agent.id]:
            w, v = result.order_totals[order_id]
            total_w += w
            total_v += v
            max_w = max(max_w, w)
            max_v = max(max_v, v)
        print(
            f"- {agent.id}: nb_commandes={len(result.assignments[agent.id])} | "
            f"poids total={total_w:.2f}kg (max commande={max_w:.2f}kg) | "
            f"volume total={total_v:.2f}dm3 (max commande={max_v:.2f}dm3)"
        )


def run_day1(warehouse: Warehouse, products: Dict[str, Product], agents: List[Agent], orders: List[Order]):
    print("\nJOUR 1 : Allocation naive (sans contraintes)")

    result = allocate_first_fit_day1(orders, agents, products)
    print("\nAllocation (First-Fit)")
    print_assignments(agents, result.assignments)

    print("\nCommandes NON assignees :", result.unassigned if len(result.unassigned) > 0 else "Aucune")

    print_day1_evaluation(orders, agents, result, products, warehouse)
    print_day1_detailed_utilization(agents, result)


def print_day2_cart_human(result):
    """Affiche les paires chariot -> humain."""
    if result.cart_human:
        print("\n== Chariots utilises (accompagnes par) ==")
        for cart_id, human_id in result.cart_human.items():
            print(f"- {cart_id} est guide par {human_id}")


def print_day2_evaluation(orders, result, products, warehouse):
    """Affiche les metriques du jour 2."""
    dist_one_way = estimate_total_distance(orders, products, warehouse)
    dist_round_trip = dist_one_way * 2
    assigned_count = sum(len(lst) for lst in result.assignments.values())

    print("\n== Evaluation Jour 2 ==")
    print(f"Nombre de commandes assignees : {assigned_count}/{len(orders)}")
    print(f"Distance estimee (aller simple) : {dist_one_way}")
    print(f"Distance estimee (aller-retour) : {dist_round_trip}")


def run_day2(warehouse: Warehouse, products: Dict[str, Product], agents: List[Agent], orders: List[Order]):
    print("\n=== JOUR 2 : Contraintes activees ===")

    result = allocate_first_fit_day2(orders, agents, products, warehouse)

    print("\n== Allocation (First-Fit + contraintes) ==")
    print_assignments(agents, result.assignments)

    if result.unassigned:
        print("\nCommandes NON assignees :", result.unassigned)

    print_day2_cart_human(result)
    print_day2_evaluation(orders, result, products, warehouse)
    print_agent_utilization(agents, result.assignments, result.order_totals)

    return result


def optimize_all_agent_routes(optimizer, agents, assignments, locations_per_agent):
    """Optimise les tournees de tous les agents et retourne les stats."""
    optimized_routes = {}
    total_distance = 0.0
    total_time = 0.0

    for agent in agents:
        if agent.id not in assignments or not assignments[agent.id]:
            continue
        locations = list(locations_per_agent.get(agent.id, set()))
        if not locations:
            continue
        route, distance, time_minutes = optimizer.optimize_agent_route(agent, locations)
        optimized_routes[agent.id] = {
            'route': route, 'distance': distance,
            'time_minutes': time_minutes, 'locations_count': len(locations)
        }
        total_distance += distance
        total_time += time_minutes
        print(f"  {agent.id} : {len(locations)} emplacements, "
              f"distance={distance:.2f}m, temps={time_minutes:.1f}min")

    return optimized_routes, total_distance, total_time


def print_day3_summary(optimized_routes, total_distance, total_time):
    """Affiche le resume des resultats du jour 3."""
    n = len(optimized_routes)
    print(f"\n  Distance totale optimisee : {total_distance:.2f}m")
    print(f"  Temps total : {total_time:.1f} minutes ({total_time/60:.1f}h)")
    print(f"  Distance moyenne par agent : {total_distance/n:.2f}m")
    print(f"  Temps moyen par agent : {total_time/n:.1f} minutes ({(total_time/n)/60:.1f}h)")


def run_day3(assignments: Dict[str, List[str]], agents: List[Agent], 
                  orders: List[Order], products: Dict[str, Product], 
                  warehouse: Warehouse):
    """Jour 3 : optimisation des tournees avec TSP."""
    print("\n" + "="*80)
    print("JOUR 3 : OPTIMISATION DES TOURNEES (TSP)")
    print("="*80)
    
    optimizer = TSPOptimizer(warehouse)
    
    print("\n[1/3] Extraction des emplacements a visiter...")
    locations_per_agent = optimizer.extract_locations(assignments, orders, products)
    
    print("\n[2/3] Optimisation des tournees avec Nearest Neighbor...")
    optimized_routes, total_distance, total_time = optimize_all_agent_routes(
        optimizer, agents, assignments, locations_per_agent
    )
    
    print("\n[3/3] Resume des resultats...")
    print_day3_summary(optimized_routes, total_distance, total_time)


def compute_load_stats(agents, assignments):
    """Calcule les stats de charge (loads, moyenne, ecart-type)."""
    agent_loads = {}
    for agent in agents:
        if agent.id in assignments:
            agent_loads[agent.id] = len(assignments[agent.id])
    avg_load = np.mean(list(agent_loads.values())) if agent_loads else 0
    std_load = np.std(list(agent_loads.values())) if agent_loads else 0
    return agent_loads, avg_load, std_load


def run_day4(assignments: Dict[str, List[str]], agents: List[Agent],
                  orders: List[Order], products: Dict[str, Product]):
    """Jour 4 : allocation optimale et regroupement."""
    print("\n" + "="*80)
    print("JOUR 4 : ALLOCATION OPTIMALE ET REGROUPEMENT (CSP)")
    print("="*80)
    
    optimizer = AllocationOptimizer()
    
    print("\n[1/2] Analyse des groupes de commandes compatibles...")
    compatible_groups = optimizer.find_compatible_orders(orders, products)
    print(f"  {len(compatible_groups)} groupes de commandes compatibles trouves")
    
    print("\n[2/2] Analyse d'equilibre de charge...")
    agent_loads, avg_load, std_load = compute_load_stats(agents, assignments)
    
    print(f"  Charge moyenne par agent : {avg_load:.1f} commandes")
    print(f"  Ecart-type : {std_load:.2f} (plus bas = mieux)")
    
    for agent_id, load in agent_loads.items():
        print(f"    {agent_id} : {load} commandes")


def print_top_products(frequency, products, n=5):
    """Affiche les n produits les plus commandes."""
    top = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:n]
    print(f"\n  Top {n} produits les plus commandes :")
    for pid, count in top:
        product = products.get(pid)
        if product:
            print(f"    - {product.name} : {count} fois")


def print_reorganization_summary(reorganization):
    """Affiche le resume de la reorganisation proposee."""
    print(f"  Produits haute frequence (a rapprocher de l'entree) : "
          f"{len(reorganization['high_frequency_products'])}")
    print(f"  Produits moyenne frequence : "
          f"{len(reorganization['medium_frequency_products'])}")
    print(f"  Produits basse frequence (eloigner) : "
          f"{len(reorganization['low_frequency_products'])}")


def print_day5_recommendations():
    """Affiche les 3 recommandations du jour 5."""
    print("\n  RECOMMANDATION 1 : Utilisation des agents")
    print("    - Les robots gerent les produits legers et accumulables")
    print("    - Les humains gerent les produits fragiles")
    print("    - Chariots : reserver pour gros volumes (surtout alimentaire)")
    
    print("\n  RECOMMANDATION 2 : Organisation des zones")
    print("    - Zone A (pres entree) : Produits tres frequents (electronique rapide)")
    print("    - Zone B (mid) : Produits moyens (livres, textiles)")
    print("    - Zone C (frigo) : Alimentaire - acces humain prioritaire")
    print("    - Zone D (loin) : Chimie - acces humain exclusif")
    print("    - Zone E (extensible) : Reserve et surplus")
    
    print("\n  RECOMMANDATION 3 : Investissements recommandes")
    print("    - +1 robot high-speed pour commandes express")
    print("    - Systeme d'etageres dynamiques (comme Kiva robots)")
    print("    - Capteurs de stock en temps reel")
    
    print("\n  RECOMMANDATION 4 : Disposition optimisee de l'entrepot")
    print("    Entrepot actuel (10x8) : 2 allees horizontales, pas de couloir vertical")
    print("    Proposition (12x10) :")
    print("    - 4 allees horizontales (y=0, 3, 6, 9) : -40% distance moyenne")
    print("    - 3 allees verticales (x=0, 5, 11) : traverse sans detour")
    print("    - Produits haute frequence en zone A/B (lignes 1-2, pres entree)")
    print("    - Chimie (D) fond gauche, loin de alimentaire (C) a droite")
    print("    - Zone libre (x=1-4, y=4-5) : allees larges pour chariots")
    print("    -> Voir data/warehouse_optimized.json et products_optimized.json")


def run_day5(orders: List[Order], products: Dict[str, Product], 
                  agents: List[Agent], warehouse: Warehouse):
    """Jour 5 : optimisation du stockage et analyse avancee."""
    print("\n" + "="*80)
    print("JOUR 5 : OPTIMISATION DU STOCKAGE ET ANALYSE AVANCEE")
    print("="*80)
    
    optimizer = StorageOptimizer()
    
    print("\n[1/3] Analyse des patterns de commandes...")
    frequency = optimizer.compute_product_frequency(orders)
    affinity = optimizer.compute_product_affinity(orders)
    
    print(f"  {len(frequency)} produits differents commandes")
    print(f"  {len(affinity)} paires de produits souvent achetees ensemble")
    
    print_top_products(frequency, products)
    
    print("\n[2/3] Proposition de reorganisation du stockage...")
    reorganization = optimizer.suggest_storage_reorganization(products, orders)
    print_reorganization_summary(reorganization)
    
    print("\n[3/3] Recommandations...")
    print_day5_recommendations()