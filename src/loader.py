import json
from pathlib import Path
from .models import Warehouse, Product, Agent, Order, Location
from typing import Dict, List

def load_json(path: str):
    """
    Charge un fichier JSON et retourne son contenu (dict ou list).

    Args:
        path (str) : Chemin (relatif ou absolu) vers le fichier JSON.

    Returns:
        dict | list : Contenu du JSON converti en objet Python.

    Raises:
        FileNotFoundError : Si le fichier n'existe pas.
        json.JSONDecodeError : Si le fichier n'est pas un JSON valide.
    """
    file_path = Path(path)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data

def JSON_to_py(warehouse: Dict, products: List[Dict], agents: List[Dict], orders: List[Dict]):
    warehouse: Warehouse = Warehouse(
        width=warehouse['dimensions']['width'],
        height=warehouse['dimensions']['height'],
        zones=warehouse['zones'],
        entry_point=Location(warehouse['entry_point'][0], warehouse['entry_point'][1]),
        aisles=warehouse['aisles'])
    products: Dict[str, Product] = {product_dict['id']: Product(
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
    agents: List[Agent] = [Agent(agent['type'], agent['id'], agent['capacity_weight'], agent['capacity_volume'], agent['speed'], agent['cost_per_hour'], agent['restrictions']) for agent in agents]
    orders: List[Order] = [Order(
        id=order_dict['id'],
        received_time=order_dict['received_time'],
        deadline=order_dict['deadline'],
        priority=order_dict['priority'],
        items=order_dict['items'],
        products=products
        )for order_dict in orders]
    
    return warehouse, products, agents, orders


if __name__ == "__main__":
    # Test de la fonction load_json
    try:
        data = load_json("data/warehouse.json")
        print("Contenu du JSON chargé avec succès :")
        print(data)
    except Exception as e:
        print(f"Erreur lors du chargement du JSON : {e}")