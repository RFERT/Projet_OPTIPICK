import json
from pathlib import Path
from typing import Dict, List, Union

from .models import Agent, Location, Order, OrderItem, Product, Warehouse


JsonType = Union[Dict, List]


def load_json(path: str | Path) -> JsonType:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_warehouse(path: str | Path) -> Warehouse:
    data = load_json(path)
    entry = Location.from_list(data["entry_point"])
    aisles = [Location.from_list(c) for c in data.get("aisles", [])]
    dims = data["dimensions"]
    return Warehouse(
        width=dims["width"],
        height=dims["height"],
        zones=data["zones"],
        entry_point=entry,
        aisles=aisles,
    )


def load_products(path: str | Path) -> Dict[str, Product]:
    data = load_json(path)
    products: Dict[str, Product] = {}
    for p in data:
        loc = Location.from_list(p["location"])
        prod = Product(
            id=p["id"],
            name=p["name"],
            category=p["category"],
            weight=p["weight"],
            volume=p["volume"],
            location=loc,
            frequency=p["frequency"],
            fragile=p["fragile"],
            incompatible_with=p.get("incompatible_with", []),
        )
        products[prod.id] = prod
    return products


def load_agents(path: str | Path) -> List[Agent]:
    data = load_json(path)
    return [Agent.from_dict(a) for a in data]


def load_orders(path: str | Path) -> List[Order]:
    data = load_json(path)
    orders: List[Order] = []
    for o in data:
        items = [OrderItem(product_id=i["product_id"], quantity=i["quantity"]) for i in o["items"]]
        orders.append(
            Order(
                id=o["id"],
                received_time=o["received_time"],
                deadline=o["deadline"],
                priority=o["priority"],
                items=items,
            )
        )
    return orders
