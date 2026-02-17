from pathlib import Path

from src.allocation import allocate_first_fit_day1
from src.loader import load_agents, load_orders, load_products, load_warehouse
from src.models import Location
from src.metrics import compute_agent_usage, estimate_total_distance
from src.utils import manhattan


def main() -> None:
    # 1) Chemins robustes (peu importe d'où tu lances python)
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    # 2) Chargement JSON -> objets Python (via loader.py + models.py)
    warehouse = load_warehouse(data_dir / "warehouse.json")
    products = load_products(data_dir / "products.json")
    agents = load_agents(data_dir / "agents.json")
    orders = load_orders(data_dir / "orders.json")

    # 3) Vérifs rapides (Jour 1.2)
    print("Warehouse:", warehouse.width, "x", warehouse.height, "| entry=", warehouse.entry_point)
    print("Products:", len(products), "| Agents:", len(agents), "| Orders:", len(orders))

    # 4) Test Manhattan (Jour 1.3)
    print("Test Manhattan =", manhattan(Location(0, 0), Location(3, 2)))

    # 5) Allocation naïve (Jour 1.4)
    result = allocate_first_fit_day1(orders, agents, products)

    assigned_count = sum(len(v) for v in result.assignments.values())
    print(f"\nAssigned: {assigned_count}/{len(orders)}")

    # Affichage simple des affectations
    for agent in agents:
        oids = result.assignments.get(agent.id, [])
        print(f"- {agent.id} ({agent.type}): {len(oids)} commande(s) -> {oids}")

    if result.unassigned:
        print("Unassigned:", result.unassigned)

    # 6) Métriques (Jour 1.5)
    dist_one_way = estimate_total_distance(orders, products, warehouse, round_trip=False)
    dist_round_trip = estimate_total_distance(orders, products, warehouse, round_trip=True)

    print("\n== Jour 1 : Évaluation ==")
    print(f"Nombre de commandes assignées : {assigned_count}/{len(orders)}")
    print(f"Distance estimée (aller simple) : {dist_one_way}")
    print(f"Distance estimée (aller-retour) : {dist_round_trip}")

    usage = compute_agent_usage(agents, result.assignments, result.order_totals)

    print("\nUtilisation par agent (poids/volume total des commandes assignées) :")
    for agent in agents:
        u = usage[agent.id]
        print(
            f"- {agent.id}: nb_commandes={int(u['orders'])} | "
            f"poids={u['weight']:.2f}/{agent.capacity_weight} | "
            f"volume={u['volume']:.2f}/{agent.capacity_volume}"
        )


if __name__ == "__main__":
    main()
