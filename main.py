from pathlib import Path
from src.allocation import allocate_first_fit_day1, allocate_first_fit_day2, estimate_total_distance, optimize_allocation_routes
from src.loader import load_json
from src.models import * 
from src.utils import *
from src.routing import extract_unique_locations, build_nodes_with_entry, compute_distance_matrix, nearest_neighbor_tsp, calculate_route_distance
import pdb
from suite import run_all_days_suite

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
    # warehouse.show()
    # print("Products:", len(products), "| Agents:", len(agents), "| Orders:", len(orders))

    print("\n=== RÉSULTATS ===")
    # pdb.set_trace()
    run_day1(warehouse, products, agents, orders)
    run_day2(warehouse, products, agents, orders)
    run_all_days_suite(assignments, agents, orders, products, warehouse)

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
        orders = result.assignments[agent.id]
        print(f"- {agent.id} ({agent.type}): {len(orders)} commande(s) -> {orders}")

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

# def run_day3(warehouse, products, agents, orders):

#     print("\n=== JOUR 3 : Optimisation des itinéraires (TSP) ===")
#     # Extraction des emplacements uniques
#     run_day3_step1(warehouse, products, agents, orders)
#     # Ajouter l'entrée (point de départ et retour)
#     run_day3_step2(warehouse, products, agents, orders)    
#     # Calculer la matrice de distances
#     run_day3_step3(warehouse, products, agents, orders)
#     # Résolution TSP (Nearest Neighbor)
#     run_day3_step4(warehouse, products, agents, orders)

# def run_day3_step1(warehouse, products, agents, orders):
#     """
#     JOUR 3 - ÉTAPE 1 : Extraire les emplacements uniques pour chaque agent.
    
#     """
#     print("\n=== JOUR 3 - ÉTAPE 1 : Extraction des emplacements uniques ===\n")
    
#     # D'abord, allocate les commandes aux agents (comme Jour 2)
#     from src.allocation import allocate_first_fit_day2
#     result = allocate_first_fit_day2(orders, agents, products, warehouse)
    
#     # Pour chaque agent, extraire les emplacements uniques
#     for agent in agents:
#         # Récupérer les IDs des commandes assignées à cet agent
#         order_ids = result.assignments[agent.id]
        
#         # Récupérer tous les produits de ces commandes
#         agent_products = []
#         for order_id in order_ids:
#             # Trouver la commande
#             found_order = next((candidate_order for candidate_order in orders if candidate_order.id == order_id), None)
#             if found_order:
#                 # Pour chaque item de la commande
#                 for item in found_order.items:
#                     # Ajouter le produit
#                     if item.product_id in products:
#                         agent_products.append(products[item.product_id])
        
#         # Extraire les emplacements uniques avec notre fonction
#         unique_locations = extract_unique_locations(agent_products)
        
#         # Afficher les résultats
#         print(f" Agent: {agent.id} (Type: {agent.type})")
#         print(f"   - Commandes assignées: {order_ids}")
#         print(f"   - Nombre de produits: {len(agent_products)}")
#         print(f"   - Emplacements uniques: {len(unique_locations)}")
#         print(f"   - Localisation des emplacements:")
#         for loc in sorted(unique_locations, key=lambda l: (l.x, l.y)):
#             print(f"      • Position ({loc.x}, {loc.y})")
#         print()

# def run_day3_step2(warehouse, products, agents, orders):
#     """
#     JOUR 3 - ÉTAPE  : Ajouter l'entrée au début ET à la fin des emplacements.
    
#     Objectif: Transformer les emplacements uniques en un CIRCUIT FERMÉ.
    
#     Cela signifie que chaque agent PART de l'entrée et DOIT Y RETOURNER.
#     """
#     print("\n=== JOUR 3 - ÉTAPE  : Ajouter l'entrée (point de départ et retour) ===\n")
    
#     # D'abord, allocate les commandes aux agents (comme Jour 2)
#     from src.allocation import allocate_first_fit_day2
#     result = allocate_first_fit_day2(orders, agents, products, warehouse)
    
#     # Pour chaque agent, construire la liste des nœuds TSP
#     for agent in agents:
#         # Récupérer les IDs des commandes assignées à cet agent
#         order_ids = result.assignments[agent.id]
        
#         # Si l'agent n'a rien à faire, passer
#         if not order_ids:
#             print(f"  Agent {agent.id}: Aucune commande (pas de tournée)")
#             continue
        
#         # Récupérer tous les produits de ces commandes
#         agent_products = []
#         for order_id in order_ids:
#             found_order = next((candidate_order for candidate_order in orders if candidate_order.id == order_id), None)
#             if found_order:
#                 for item in found_order.items:
#                     if item.product_id in products:
#                         agent_products.append(products[item.product_id])
        
#         # ÉTAPE  : Extraire les emplacements uniques
#         unique_locations = extract_unique_locations(agent_products)
        
#         # ÉTAPE  : Ajouter l'entrée au début ET à la fin
#         nodes = build_nodes_with_entry(warehouse.entry_point, unique_locations)
        
#         # Afficher les résultats
#         print(f" Agent: {agent.id} (Type: {agent.type})")
#         print(f"   ├─ Étape  (extraction) : {len(unique_locations)} emplacements uniques")
#         print(f"   └─ Étape  (circuit) : {len(nodes)} nœuds TSP (avec entrée début + fin)")
#         print(f"\n     Séquence de nœuds pour le TSP :")
        
#         for i, node in enumerate(nodes):
#             if i == 0:
#                 print(f"       [{i}]  DÉPART (Entrée)  : {node}")
#             elif i == len(nodes) - 1:
#                 print(f"       [{i}]  RETOUR (Entrée)  : {node}")
#             else:
#                 # Trouver quel produit est à ce nœud
#                 print(f"       [{i}]  Emplacement      : {node}")
        
#         print()

# def run_day3_step3(warehouse, products, agents, orders):
#     """
#     JOUR 3 - ÉTAPE : Calculer la matrice de distances Manhattan.
#     """
#     print("\n=== JOUR 3 - ÉTAPE  : Calculer la matrice de distances ===\n")
    
#     # D'abord, allocate les commandes aux agents (comme Jour 2)
#     from src.allocation import allocate_first_fit_day2
#     result = allocate_first_fit_day2(orders, agents, products, warehouse)
    
#     # Pour chaque agent, construire et afficher la matrice de distances
#     for agent in agents:
#         # Récupérer les IDs des commandes assignées à cet agent
#         order_ids = result.assignments[agent.id]
        
#         # Si l'agent n'a rien à faire, passer
#         if not order_ids:
#             continue
        
#         # Récupérer tous les produits de ces commandes
#         agent_products = []
#         for order_id in order_ids:
#             found_order = next((candidate_order for candidate_order in orders if candidate_order.id == order_id), None)
#             if found_order:
#                 for item in found_order.items:
#                     if item.product_id in products:
#                         agent_products.append(products[item.product_id])
        
#         # Étapes précédentes
#         unique_locations = extract_unique_locations(agent_products)
#         nodes = build_nodes_with_entry(warehouse.entry_point, unique_locations)
        
#         # ÉTAPE  : Calculer la matrice de distances
#         distance_matrix = compute_distance_matrix(nodes)
        
#         # Afficher les résultats
#         print(f" Agent: {agent.id} (Type: {agent.type})")
#         print(f"   • Nombre de nœuds : {len(nodes)}")
#         print(f"   • Taille matrice : {len(distance_matrix)} x {len(distance_matrix[0])}")
        
#         # Afficher la matrice complète si elle n'est pas trop grande
#         if len(nodes) <= 6:
#             print(f"\n    Matrice de distances (complète) :")
            
#             # En-têtes des colonnes
#             header = "      "
#             for col_index in range(len(nodes)):
#                 header += f"[{col_index}]  "
#             print(header)
            
#             # Lignes de la matrice
#             for row_index, row in enumerate(distance_matrix):
#                 line = f"   [{row_index}]  "
#                 for dist in row:
#                     line += f"{dist:3d}  "
#                 print(line)
#         else:
#             # Pour les grandes matrices, afficher des statistiques
#             all_distances = []
#             for row in distance_matrix:
#                 all_distances.extend(row)
            
#             print(f"\n    Statistiques de la matrice (trop grande pour affichage complet) :")
#             print(f"       • Distance minimum : {min(all_distances)}")
#             print(f"       • Distance maximum : {max(all_distances)}")
#             print(f"       • Distance moyenne : {sum(all_distances) / len(all_distances):.1f}")
            
#             # Afficher un petit exemple
#             print(f"\n    Exemples de distances (premiers 4 nœuds) :")
#             for row_index in range(min(4, len(distance_matrix))):
#                 line = f"       Du nœud [{row_index}] : "
#                 for col_index in range(min(4, len(distance_matrix[0]))):
#                     line += f"{distance_matrix[row_index][col_index]:3d}  "
#                 print(line)
        
#         print()

# def run_day3_step4(warehouse, products, agents, orders):
    """
    JOUR 3 - ÉTAPE 4 : Résoudre le TSP avec l'heuristique du PLUS PROCHE VOISIN.
    
    Algorithme Nearest Neighbor :
        1. Commencer à l'entrée (point de départ)
        2. À chaque étape, aller à l'emplacement non visité le plus proche
        3. Répéter jusqu'à visiter tous les emplacements
        4. Retourner à l'entrée
    """
    print("\n=== JOUR 3 - ÉTAPE 4 : Résolution TSP (Nearest Neighbor) ===\n")
    
    # D'abord, allocate les commandes aux agents (comme Jour 2)
    from src.allocation import allocate_first_fit_day2
    result = allocate_first_fit_day2(orders, agents, products, warehouse)
    
    # Pour chaque agent, résoudre son TSP personnel
    for agent in agents:
        # Récupérer les IDs des commandes assignées à cet agent
        order_ids = result.assignments[agent.id]
        
        # Si l'agent n'a rien à faire, passer
        if not order_ids:
            print(f"  Agent {agent.id}: Aucune commande (pas de tournée)")
            continue
        
        # Récupérer tous les produits de ces commandes
        agent_products = []
        for order_id in order_ids:
            found_order = next((candidate_order for candidate_order in orders if candidate_order.id == order_id), None)
            if found_order:
                for item in found_order.items:
                    if item.product_id in products:
                        agent_products.append(products[item.product_id])
        
        # Étapes précédentes
        unique_locations = extract_unique_locations(agent_products)
        nodes = build_nodes_with_entry(warehouse.entry_point, unique_locations)
        
        # ÉTAPE 4 : Résoudre le TSP avec Nearest Neighbor
        route_indices, total_distance = nearest_neighbor_tsp(nodes, start_index=0)
        
        # Afficher les résultats
        print(f" Agent: {agent.id} (Type: {agent.type})")
        print(f"   • Commandes assignées: {order_ids}")
        print(f"   • Emplacements uniques à visiter: {len(unique_locations)}")
        print(f"\n   ✅ ROUTE OPTIMISÉE (Nearest Neighbor) :")
        
        total_dist = 0
        for step, idx in enumerate(route_indices):
            node = nodes[idx]
            
            if step == 0:
                label = "🔴 DÉPART (Entrée)"
            elif step == len(route_indices) - 1:
                label = "🔴 RETOUR (Entrée)"
            else:
                label = "📍 Arrêt"
            
            print(f"       Étape {step}: {label:25} → Position {node}")
            
            # Afficher la distance jusqu'au prochain point
            if step < len(route_indices) - 1:
                next_idx = route_indices[step + 1]
                segment_distance = manhattan(nodes[idx], nodes[next_idx])
                total_dist += segment_distance
                print(f"                   Distance: {segment_distance} unités")
        
        print(f"\n   📊 Distance totale du parcours optimal : {total_distance} unités")
        print(f"   📈 Cette tournée visite {len(unique_locations)} emplacements différents")
        print()


if __name__ == "__main__":
    main()
