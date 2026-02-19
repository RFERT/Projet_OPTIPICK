from pathlib import Path

from src.allocation import allocate_first_fit_day1, allocate_first_fit_day2, estimate_total_distance, optimize_allocation_routes
from src.loader import load_json
from src.models import Agent, Order, OrderItem, Product, Team, Warehouse
from src.models import Location
from src.utils import manhattan
from src.routing import nearest_neighbor_tsp, calculate_route_distance


# ---------------------------
# Jour 1 (naïf)
# ---------------------------
def run_day1(warehouse, products, team, orders):
    print("\n=== JOUR 1 : Allocation naïve (sans contraintes) ===")

    result = allocate_first_fit_day1(orders, team, products)
    
    # Optimiser les itinéraires (TSP) avec l'heuristique du Plus Proche Voisin
    result = optimize_allocation_routes(result, orders, products, warehouse)

    print("\n== Allocation (First-Fit) ==")
    for agent in team.agents.values():
        oids = result.assignments[agent.id]
        print(f"- {agent.id} ({agent.type}): {len(oids)} commande(s) -> {oids}")

    if result.unassigned:
        print("\n❗ Commandes NON assignées :", result.unassigned)

    dist_one_way = estimate_total_distance(orders, products, warehouse, round_trip=False)
    dist_round_trip = estimate_total_distance(orders, products, warehouse, round_trip=True)
    assigned_count = sum(len(v) for v in result.assignments.values())

    print("\n== Évaluation Jour 1 ==")
    print(f"Nombre de commandes assignées : {assigned_count}/{len(orders)}")
    print(f"Distance estimée (aller simple) : {dist_one_way}")
    print(f"Distance estimée (aller-retour) : {dist_round_trip}")

    print("\nOptimisation TSP par agent (Plus Proche Voisin) :")
    for agent in team.agents.values():
        if agent.id in result.routes:
            route_info = result.routes[agent.id]
            route_distance = route_info['distance']
            route_length = len(route_info['route'])
            print(f"- {agent.id}: Distance TSP = {route_distance}, Emplacements visités = {route_length - 2}")

    print("\nUtilisation par agent (poids/volume total des commandes assignées) :")
    for agent in team.agents.values():
        total_w = 0.0
        total_v = 0.0
        for oid in result.assignments[agent.id]:
            w, v = result.order_totals[oid]
            total_w += w
            total_v += v

        print(
            f"- {agent.id}: nb_commandes={len(result.assignments[agent.id])} | "
            f"poids={total_w:.2f}/{agent.capacity_weight} | "
            f"volume={total_v:.2f}/{agent.capacity_volume}"
        )


# ---------------------------
# Jour 2 (contraintes)
# ---------------------------
def run_day2(warehouse, products, agents, orders):
    print("\n=== JOUR 2 : Contraintes activées ===")

    result = allocate_first_fit_day2(orders, agents, products, warehouse)
    
    # Optimiser les itinéraires (TSP) avec l'heuristique du Plus Proche Voisin
    result = optimize_allocation_routes(result, orders, products, warehouse)

    print("\n== Allocation (First-Fit + contraintes) ==")
    for agent in agents:
        oids = result.assignments[agent.id]
        print(f"- {agent.id} ({agent.type}): {len(oids)} commande(s) -> {oids}")

    if result.unassigned:
        print("\n❗ Commandes NON assignées :", result.unassigned)

    # ✅ Affichage cart -> human (indépendant de unassigned)
    if result.cart_human:
        print("\n== Chariots utilisés (accompagnés par) ==")
        for cart_id, human_id in result.cart_human.items():
            print(f"- {cart_id} est guidé par {human_id}")

    dist_one_way = estimate_total_distance(orders, products, warehouse, round_trip=False)
    dist_round_trip = estimate_total_distance(orders, products, warehouse, round_trip=True)
    assigned_count = sum(len(v) for v in result.assignments.values())

    print("\n== Évaluation Jour 2 ==")
    print(f"Nombre de commandes assignées : {assigned_count}/{len(orders)}")
    print(f"Distance estimée (aller simple) : {dist_one_way}")
    print(f"Distance estimée (aller-retour) : {dist_round_trip}")

    print("\nOptimisation TSP par agent (Plus Proche Voisin) :")
    for agent in agents:
        if agent.id in result.routes:
            route_info = result.routes[agent.id]
            route_distance = route_info['distance']
            route_length = len(route_info['route'])
            print(f"- {agent.id}: Distance TSP = {route_distance}, Emplacements visités = {route_length - 2}")

    print("\nUtilisation par agent (poids/volume total des commandes assignées) :")
    for agent in agents:
        total_w = 0.0
        total_v = 0.0
        for oid in result.assignments[agent.id]:
            w, v = result.order_totals[oid]
            total_w += w
            total_v += v

        print(
            f"- {agent.id}: nb_commandes={len(result.assignments[agent.id])} | "
            f"poids={total_w:.2f}/{agent.capacity_weight} | "
            f"volume={total_v:.2f}/{agent.capacity_volume}"
        )


# ---------------------------
# Jour 3 (Test TSP)
# ---------------------------
def run_day3(warehouse):
    """
    Jour 3 : Test complet de l'algorithme TSP (Nearest Neighbor)
    """
    print("\n=== JOUR 3 : Test TSP - Plus Proche Voisin ===\n")
    
    # Points d'entrée (entrepôt)
    entry = warehouse.entry_point
    
    # Emplacements à visiter (exemple)
    locations = [
        Location(2, 1),
        Location(1, 0),
        Location(4, 0),
        Location(3, 4),
        Location(2, 3),
    ]
    
    print("Entrée de l'entrepôt:", entry)
    print("Emplacements à visiter:")
    for i, loc in enumerate(locations):
        print(f"  {i+1}. {loc}")
    
    # Résoudre le TSP
    route = nearest_neighbor_tsp(locations, entry, manhattan)
    distance = calculate_route_distance(route, manhattan)
    
    print("\n=== Résultats ===")
    print("Route optimisée:")
    for i, loc in enumerate(route):
        if i == 0:
            print(f"  Départ: {loc}")
        elif i == len(route) - 1:
            print(f"  Retour: {loc}")
        else:
            print(f"  {i}. {loc}")
    
    print(f"\nDistance totale: {distance}")
    print(f"Nombre de visites: {len(route) - 2} (entrée, sortie non comptées)")
    print("\n✅ Test TSP - Plus Proche Voisin réussi !")


# ---------------------------
# Main
# ---------------------------
def main():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    warehouse_json = load_json(data_dir / "warehouse.json")
    products_list = load_json(data_dir / "products.json")
    agents = load_json(data_dir / "agents.json")
    orders = load_json(data_dir / "orders.json")
    
    # Convert products list to dictionary with Product objects
    products = {
        p['id']: Product(
            id=p['id'],
            name=p['name'],
            category=p['category'],
            weight=p['weight'],
            volume=p['volume'],
            location=Location(p['location'][0], p['location'][1]),
            frequency=p['frequency'],
            fragile=p['fragile'],
            incompatible_with=p.get('incompatible_with', [])
        )
        for p in products_list
    }
    
    team = Team(agents)
    warehouse = Warehouse(
        width=warehouse_json['dimensions']['width'],
        height=warehouse_json['dimensions']['height'],
        zones=warehouse_json['zones'],
        entry_point=Location(warehouse_json['entry_point'][0], warehouse_json['entry_point'][1])
    )  
    # Convert order dictionaries and item dictionaries to Order and OrderItem objects
    orders = [
        Order(
            id=o['id'],
            received_time=o['received_time'],
            deadline=o['deadline'],
            priority=o['priority'],
            items=[OrderItem(product_id=item['product_id'], quantity=item['quantity'], zone=None) for item in o['items']]
        )
        for o in orders
    ]

    print("Warehouse:", warehouse.width, "x", warehouse.height, "| entry=", warehouse.entry_point)
    print("Products:", len(products), "| Agents:", len(agents), "| Orders:", len(orders))
    print("Test Manhattan =", manhattan(Location(0, 0), Location(3, 2)))

    print("\n==============================")
    print("Comparaison : Jour 1 vs Jour 2")
    print("==============================")

    run_day1(warehouse, products, team, orders)
    run_day2(warehouse, products, team.agents.values(), orders)
    run_day3(warehouse)


if __name__ == "__main__":
    main()




