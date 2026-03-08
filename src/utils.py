
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
    return abs(a.x - b.x) + abs(a.y - b.y)

