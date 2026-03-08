from pathlib import Path
from src.allocation import *
from src.loader import *
from src.models import * 
from src.utils import *
from src.routing import *
from src.optimization import AllocationOptimizer
from src.storage import StorageOptimizer
import numpy as np

def main():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    # JSON -> DICT
    warehouse = load_json(data_dir / "warehouse.json")
    products = load_json(data_dir / "products.json")
    agents = load_json(data_dir / "agents.json")
    orders = load_json(data_dir / "orders.json")
    print("Données chargées depuis JSON")

    # DICT(JSON) -> objets python
    warehouse, products, agents, orders = JSON_to_py(warehouse, products, agents, orders)
    print("Données converties en objets Python")

    print("\n=== RÉSULTATS ===")
    
    # JOURS 1-2 : Allocation
    run_day1(warehouse, products, agents, orders)
    result_day2 = run_day2(warehouse, products, agents, orders)
    
    # JOURS 3-5 : Orchestrateurs éclatés directement dans main()
    run_day3_main(result_day2.assignments, agents, orders, products, warehouse)
    run_day4_main(result_day2.assignments, agents, orders, products)
    run_day5_main(orders, products, agents, warehouse)

def run_day1(warehouse: Warehouse, products: Dict[str, Product], agents: List[Agent], orders: List[Order]):
    print("\nJOUR 1 : Allocation naïve (sans contraintes)")

    # pdb.set_trace()
    result = allocate_first_fit_day1(orders, agents, products)
    print("\nAllocation (First-Fit)")
    for agent in agents:
        agent_orders = result.assignments[agent.id]
        print(f"- {agent.id} ({agent.type}): {len(agent_orders)} commande(s) -> {agent_orders}")

    
    print("\nCommandes NON assignées :", result.unassigned if len(result.unassigned) > 0 else "Aucune")

    dist_one_way = estimate_total_distance(orders, products, warehouse)
    assigned_count = sum(len(assignment_list) for assignment_list in result.assignments.values())

    print("\nÉvaluation Jour 1")
    print(f"Nombre de commandes assignées : {assigned_count}/{len(orders)}")
    print(f"Distance estimée (Allers retours pour chaque produit) : {dist_one_way}")

    print("\nUtilisation par agent (poids/volume total des commandes assignées) :")
    for agent in agents:
        total_w = 0.0
        total_v = 0.0
        max_w = 0.0
        max_v = 0.0
        
        for order in result.assignments[agent.id]:
            w, v = result.order_totals[order]
            total_w += w
            total_v += v
            max_w = max(max_w, w)
            max_v = max(max_v, v)

        print(
            f"- {agent.id}: nb_commandes={len(result.assignments[agent.id])} | "
            f"poids total={total_w:.2f}kg (max commande={max_w:.2f}kg) | "
            f"volume total={total_v:.2f}dm³ (max commande={max_v:.2f}dm³)"
        )

def run_day2(warehouse: Warehouse, products: Dict[str, Product], agents: List[Agent], orders: List[Order]):
    print("\n=== JOUR 2 : Contraintes activées ===")

    result = allocate_first_fit_day2(orders, agents, products, warehouse)

    print("\n== Allocation (First-Fit + contraintes) ==")
    for agent in agents:
        agent_orders = result.assignments[agent.id]
        print(f"- {agent.id} ({agent.type}): {len(agent_orders)} commande(s) -> {agent_orders}")

    if result.unassigned:
        print("\n❗ Commandes NON assignées :", result.unassigned)

    # ✅ Affichage cart -> human (indépendant de unassigned)
    if result.cart_human:
        print("\n== Chariots utilisés (accompagnés par) ==")
        for cart_id, human_id in result.cart_human.items():
            print(f"- {cart_id} est guidé par {human_id}")

    dist_one_way = estimate_total_distance(orders, products, warehouse)
    dist_round_trip = estimate_total_distance(orders, products, warehouse) * 2  # Aller-retour pour chaque produit
    assigned_count = sum(len(assignment_list) for assignment_list in result.assignments.values())

    print("\n== Évaluation Jour 2 ==")
    print(f"Nombre de commandes assignées : {assigned_count}/{len(orders)}")
    print(f"Distance estimée (aller simple) : {dist_one_way}")
    print(f"Distance estimée (aller-retour) : {dist_round_trip}")

    print("\nUtilisation par agent (poids/volume total des commandes assignées) :")
    for agent in agents:
        total_w = 0.0
        total_v = 0.0
        for order in result.assignments[agent.id]:
            w, v = result.order_totals[order]
            total_w += w
            total_v += v

        print(
            f"- {agent.id}: nb_commandes={len(result.assignments[agent.id])} | "
            f"poids={total_w:.2f}/{agent.capacity_weight} | "
            f"volume={total_v:.2f}/{agent.capacity_volume}"
        )

    return result



def run_day3_main(assignments: Dict[str, List[str]], agents: List[Agent], 
                  orders: List[Order], products: Dict[str, Product], 
                  warehouse: Warehouse):
    """
    JOUR 3 : Optimisation des tournées avec TSP.
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


def run_day4_main(assignments: Dict[str, List[str]], agents: List[Agent],
                  orders: List[Order], products: Dict[str, Product]):
    """
    JOUR 4 : Allocation optimale et regroupement.
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


def run_day5_main(orders: List[Order], products: Dict[str, Product], 
                  agents: List[Agent], warehouse: Warehouse):
    """
    JOUR 5 : Optimisation du stockage et analyse avancée.
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


if __name__ == "__main__":
    main()
