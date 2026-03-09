from __future__ import annotations
from typing import Dict, List
from random import randint
import matplotlib.pyplot as plt
import numpy as np

class Location:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, Location):
            return self.x == other.x and self.y == other.y
        return False

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Location(x={self.x}, y={self.y})"


class Warehouse:
    def __init__(self, width: int, height: int, zones: Dict[str, Dict], entry_point: Location, aisles: list[list[int]]):
        self.width: int = width
        self.height: int = height
        self.zones: Dict[str, Dict] = zones          # brut (jour 1)
        self.entry_point: Location = entry_point

        self.grid = np.array([[""for column in range(width)]for row in range(height)])
        for zone_name, zone_data in zones.items():
            for coord in zone_data["coords"]:
                self.grid[coord[1]][coord[0]] = zone_name
        self.grid[entry_point.y][entry_point.x] = "1"
        for coord in aisles:
            self.grid[coord[1]][coord[0]] = "0"
            
    def show(self):
        color_map = {
        'A': 0,  # Bleu - electronique
        'B': 1,  # Marron - Livres
        'C': 2,  # Vert - Alimentaire
        'D': 3,  # Rouge - Chimie
        'E': 4,  # Orange - Textile
        '0': 5,  # Blanc - Allee
        '1': 6,   # Violet - Entree
        '': 7   # Gris - Erreur (non défini)
        }

        warehouse_colors = [[color_map[cell] for cell in row] for row in self.grid]
        plt.imshow(warehouse_colors, cmap='tab10')
        cbar = plt.colorbar()
        cbar.set_ticks([0,1,2,3,4,5,6,7])
        cbar.set_ticklabels(["A","B","C","D","E","Allée","Entrée","Erreur"])
        # plt.colorbar()
        plt.show()

class Agent:
    def __init__(self, type: str, id: str, capacity_weight: float, capacity_volume: float, speed: float, cost_per_hour: float, restrictions: List[str]):
        self.type: str = type
        self.id: str = id
        self.capacity_weight: float = capacity_weight
        self.capacity_volume: float = capacity_volume
        self.speed: float = speed
        self.cost_per_hour: float = cost_per_hour
        self.restrictions: List[str] = restrictions

class Product:
    def __init__(self, id: str, name: str, category: str, weight: float, 
                 volume: float, location: Location, frequency: str, fragile: bool, 
                 incompatible_with: List[str] = None):
        self.id = id
        self.name = name
        self.category = category
        self.weight = weight
        self.volume = volume
        self.location = location
        self.frequency = frequency
        self.fragile = fragile
        self.incompatible_with = incompatible_with if incompatible_with is not None else []

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name})"

    def __eq__(self, other):
        if isinstance(other, Product):
            return self.id == other.id
        return False

class OrderItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity


    def __eq__(self, other):
        if isinstance(other, OrderItem):
            return (self.product == other.product and 
                    self.quantity == other.quantity)
        return False

    def __hash__(self):
        return hash((self.product, self.quantity))

    def __repr__(self):
        return f"OrderItem(product_id={self.product}, quantity={self.quantity})"


class Order:
    def __init__(self, id: str, received_time: str, deadline: str, priority: str, items: List[Dict], products: Dict[str, Product]):
        self.id: str = id
        self.received_time: str = received_time
        self.deadline: str = deadline
        self.priority: str = priority
        self.items: List[OrderItem] = []
        for item in items:
            self.items.append(OrderItem(products[item['product_id']], item['quantity']))

    def __repr__(self):
        return f"Order(id={self.id}, priority={self.priority})"
