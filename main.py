from pathlib import Path

from src.allocation import allocate_first_fit, estimate_total_distance
from src.loader import load_agents, load_orders, load_products, load_warehouse
from src.models import Location
from src.utils import manhattan


def main():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    # 1.1 Chargement
    warehouse = load_warehouse(data_dir / "warehouse.json")
    products = load_products(data_dir / "products.json")
    agents = load_agents(data_dir / "agents.json")
    orders = load_orders(data_dir / "orders.json")

    print("=== OPTIPICK — JOUR 1 ===")
    print(f"Warehouse: {warehouse.width}x{warehouse.height} | entry={warehouse.entry_point}")
    print(f"Products:  {len(products)}")
    print(f"Agents:    {len(agents)}")
    print(f"Orders:    {len(orders)}")

    # 1.3 Distance Manhattan (test)
    a = Location(0, 0)
    b = Location(3, 2)
    print("\nTest Manhattan (0,0)->(3,2) =", manhattan(a, b))

    # 1.4 Allocation naïve First-Fit
    result = allocate_first_fit(orders, agents, products)

    print("\n== Allocation (First-Fit) ==")
    for agent in agents:
        oids = result.assignments[agent.id]
        print(f"- {agent.id} ({agent.type}): {len(oids)} commande(s) -> {oids}")

    if result.unassigned:
        print("\n❗ Commandes NON assignées (aucun agent n'a la capacité) :", result.unassigned)

    # 1.5 Évaluation
    assigned_count = sum(len(v) for v in result.assignments.values())
    total_distance_est = estimate_total_distance(orders, products, warehouse)

    print("\n== Évaluation (Jour 1.5) ==")
    print(f"Nombre de commandes assignées : {assigned_count}/{len(orders)}")
    print(f"Distance totale estimée (entrée -> produits) : {total_distance_est}")

    print("\nUtilisation par agent (poids/volume total des commandes assignées) :")
    # index rapide des commandes
    orders_by_id = {o.id: o for o in orders}

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


if __name__ == "__main__":
    main()


