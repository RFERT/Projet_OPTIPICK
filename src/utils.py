from .models import *


def manhattan(a: Location, b: Location) -> int:
    """Distance Manhattan sur une grille : |x1-x2| + |y1-y2|."""
    return abs(a.x - b.x) + abs(a.y - b.y)

def JSON_to_py():
        warehouse = Warehouse(
        width=warehouse['dimensions']['width'],
        height=warehouse['dimensions']['height'],
        zones=warehouse['zones'],
        entry_point=Location(warehouse['entry_point'][0], warehouse['entry_point'][1])    )
        products = {
        product_dict['id']: Product(
            id=product_dict['id'],
            name=product_dict['name'],
            category=product_dict['category'],
            weight=product_dict['weight'],
            volume=product_dict['volume'],
            location=Location(product_dict['location'][0], product_dict['location'][1]),
            frequency=product_dict['frequency'],
            fragile=product_dict['fragile'],
            incompatible_with=product_dict.get('incompatible_with', [])
        )
        for product_dict in products
    }
        team = Team(agents)
        orders = [Order(
            id=order_dict['id'],
            received_time=order_dict['received_time'],
            deadline=order_dict['deadline'],
            priority=order_dict['priority'],
            items=order_dict['items']) for order_dict in orders]