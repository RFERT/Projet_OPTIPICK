from pathlib import Path

from src.loader import load_agents, load_orders, load_products, load_warehouse
from src.models import Location
from src.utils import manhattan
from src.allocation import allocate_first_fit_day1


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    warehouse = load_warehouse(data_dir / "warehouse.json")
    products = load_products(data_dir / "products.json")
    agents = load_agents(data_dir / "agents.json")
    orders = load_orders(data_dir / "orders.json")

    print("Warehouse:", warehouse.width, "x", warehouse.height, "| entry=", warehouse.entry_point)
    print("Products:", len(products), "| Agents:", len(agents), "| Orders:", len(orders))

    # Test Manhattan (étape 1.3)
    print("Test Manhattan =", manhattan(Location(0, 0), Location(3, 2)))

    # Jour 1 : allocation naïve
    result = allocate_first_fit_day1(orders, agents, products)
    assigned_count = sum(len(v) for v in result.assignments.values())
    print("Assigned:", assigned_count, "/", len(orders))
    if result.unassigned:
        print("Unassigned:", result.unassigned)


if __name__ == "__main__":
    main()
