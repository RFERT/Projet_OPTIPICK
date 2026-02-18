from pathlib import Path

from src.allocation import allocate_first_fit_day1, allocate_first_fit_day2, estimate_total_distance
from src.loader import load_json
from src.models import Agent, Order, Product, Team, Warehouse
from src.models import Location
from src.utils import manhattan


# ---------------------------
# Jour 1 (naïf)
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
    products = load_json(data_dir / "products.json")
    agents = load_json(data_dir / "agents.json")
    orders = load_json(data_dir / "orders.json")
    team = Team(agents)
    warehouse = Warehouse(
        width=warehouse_json['dimensions']['width'],
        height=warehouse_json['dimensions']['height'],
        zones=warehouse_json['zones'],
        entry_point=Location(warehouse_json['entry_point']['x'], warehouse_json['entry_point']['y'])
    )  
    orders = [Order(**o) for o in orders]

    print("Warehouse:", warehouse.width, "x", warehouse.height, "| entry=", warehouse.entry_point)
    print("Products:", len(products), "| Agents:", len(agents), "| Orders:", len(orders))
    print("Test Manhattan =", manhattan(Location(0, 0), Location(3, 2)))

    print("\n==============================")
    print("Comparaison : Jour 1 vs Jour 2")
    print("==============================")

    run_day1(warehouse, products, team, orders)
    run_day2(warehouse, products, team.agents.values(), orders)


if __name__ == "__main__":
    main()




