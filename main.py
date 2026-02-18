from pathlib import Path

from src.allocation import allocate_first_fit_day1, allocate_first_fit_day2, estimate_total_distance
from src.loader import load_json
from src.models import Agent, Order, OrderItem, Product, Team, Warehouse
from src.models import Location
from src.utils import manhattan
from src.routing import extract_unique_locations
# ---------------------------
def run_day1(warehouse, products, team, orders):
    print("\n=== JOUR 1 : Allocation naïve (sans contraintes) ===")

    result = allocate_first_fit_day1(orders, team, products)

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
    
    # Jour 3 - Étape 1: Extraction des emplacements uniques
    run_day3_step1(warehouse, products, team, orders)


# ---------------------------
# Jour 3 - Étape 1 : Extraction des emplacements uniques
# ---------------------------
def run_day3_step1(warehouse, products, team, orders):
    """
    JOUR 3 - ÉTAPE 1 : Extraire les emplacements uniques pour chaque agent.
    
    """
    print("\n=== JOUR 3 - ÉTAPE 1 : Extraction des emplacements uniques ===\n")
    
    # D'abord, allocate les commandes aux agents (comme Jour 2)
    from src.allocation import allocate_first_fit_day2
    result = allocate_first_fit_day2(orders, list(team.agents.values()), products, warehouse)
    
    # Pour chaque agent, extraire les emplacements uniques
    for agent in team.agents.values():
        # Récupérer les IDs des commandes assignées à cet agent
        order_ids = result.assignments[agent.id]
        
        # Récupérer tous les produits de ces commandes
        agent_products = []
        for order_id in order_ids:
            # Trouver la commande
            order = next((o for o in orders if o.id == order_id), None)
            if order:
                # Pour chaque item de la commande
                for item in order.items:
                    # Ajouter le produit
                    if item.product_id in products:
                        agent_products.append(products[item.product_id])
        
        # Extraire les emplacements uniques avec notre fonction
        unique_locations = extract_unique_locations(agent_products)
        
        # Afficher les résultats
        print(f" Agent: {agent.id} (Type: {agent.type})")
        print(f"   - Commandes assignées: {order_ids}")
        print(f"   - Nombre de produits: {len(agent_products)}")
        print(f"   - Emplacements uniques: {len(unique_locations)}")
        print(f"   - Localisation des emplacements:")
        for loc in sorted(unique_locations, key=lambda l: (l.x, l.y)):
            print(f"      • Position ({loc.x}, {loc.y})")
        print()


if __name__ == "__main__":
    main()




