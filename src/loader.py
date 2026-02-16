import json
from pathlib import Path
from typing import Dict, List

from .models import Agent, Cart, Human, Location, Order, OrderItem, Product, Robot, Warehouse


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_warehouse(path: Path) -> Warehouse:
    data = _load_json(path)

    width = int(data["dimensions"]["width"])
    height = int(data["dimensions"]["height"])
    zones = data.get("zones", {})

    ep = data["entry_point"]
    entry_point = Location(int(ep[0]), int(ep[1]))

    return Warehouse(width=width, height=height, zones=zones, entry_point=entry_point)


def load_products(path: Path) -> Dict[str, Product]:
    data = _load_json(path)

    products: Dict[str, Product] = {}
    for p in data:
        prod = Product(
            id=p["id"],
            name=p.get("name", ""),
            category=p.get("category", ""),
            weight=float(p.get("weight", 0.0)),
            volume=float(p.get("volume", 0.0)),
            location=Location(int(p["location"][0]), int(p["location"][1])),
            frequency=p.get("frequency", "unknown"),
            fragile=bool(p.get("fragile", False)),
            incompatible_with=list(p.get("incompatible_with", [])),
        )
        products[prod.id] = prod

    return products


def _agent_factory(a: dict) -> Agent:
    common = dict(
        id=a["id"],
        type=a["type"],
        capacity_weight=float(a.get("capacity_weight", 0.0)),
        capacity_volume=float(a.get("capacity_volume", 0.0)),
        speed=float(a.get("speed", 1.0)),
        cost_per_hour=float(a.get("cost_per_hour", 0.0)),
        restrictions=dict(a.get("restrictions", {})),
    )

    if common["type"] == "robot":
        return Robot(**common)
    if common["type"] == "human":
        return Human(**common)
    if common["type"] == "cart":
        return Cart(**common)

    # fallback
    return Agent(**common)


def load_agents(path: Path) -> List[Agent]:
    data = _load_json(path)
    return [_agent_factory(a) for a in data]


def load_orders(path: Path) -> List[Order]:
    data = _load_json(path)

    orders: List[Order] = []
    for o in data:
        items = [
            OrderItem(product_id=i["product_id"], quantity=int(i["quantity"]))
            for i in o.get("items", [])
        ]

        orders.append(
            Order(
                id=o["id"],
                received_time=o.get("received_time", "00:00"),
                deadline=o.get("deadline", "23:59"),
                priority=o.get("priority", "standard"),
                items=items,
            )
        )

    return orders
