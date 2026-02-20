
from src.models import *
from typing import Tuple
import pdb

def compute_order_totals(order: Order, products: Dict[str, Product]) -> Tuple[float, float]:
    total_w = 0.0
    total_v = 0.0
    for it in order.items:
        p = products[it.product.id]
        total_w += p.weight * it.quantity
        total_v += p.volume * it.quantity
    return total_w, total_v

def manhattan(a: Location, b: Location) -> int:
    """Distance Manhattan sur une grille : |x1-x2| + |y1-y2|."""
    return abs(a.x - b.x) + abs(a.y - b.y)

def JSON_to_py(warehouse: Dict, products: List[Dict], agents: List[Dict], orders: List[Dict]):
    warehouse = Warehouse(
        width=warehouse['dimensions']['width'],
        height=warehouse['dimensions']['height'],
        zones=warehouse['zones'],
        entry_point=Location(warehouse['entry_point'][0], warehouse['entry_point'][1]),
        aisles=warehouse['aisles'])
    products = {product_dict['id']: Product(
        id=product_dict['id'],
        name=product_dict['name'],
        category=product_dict['category'],
        weight=product_dict['weight'],
        volume=product_dict['volume'],
        location=Location(product_dict['location'][0], product_dict['location'][1]),
        frequency=product_dict['frequency'],
        fragile=product_dict['fragile'],
        incompatible_with=product_dict.get('incompatible_with', [])
        )for product_dict in products}
    # pdb.set_trace()
    agents = [Agent(agent['type'], agent['id'], agent['capacity_weight'], agent['capacity_volume'], agent['speed'], agent['cost_per_hour'], agent['restrictions']) for agent in agents]
    # je crois que agents est une liste de dicts, pas un dict d'agents
    # agents = [{agent['id']: Agent(
    #     id=agent['id'],
    #     type=agent['type'],
    #     capacity_weight=agent['capacity_weight'],
    #     capacity_volume=agent['capacity_volume'],
    #     speed=agent['speed'],
    #     cost_per_hour=agent['cost_per_hour'],
    #     restrictions=agent['restrictions']
    # )} for agent in agents]
    orders = [Order(
        id=order_dict['id'],
        received_time=order_dict['received_time'],
        deadline=order_dict['deadline'],
        priority=order_dict['priority'],
        items=order_dict['items'],
        products=products
        )for order_dict in orders]
    
    return warehouse, products, agents, orders
