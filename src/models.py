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
    def __init__(self, width: int, height: int, zones: Dict[str, Dict], entry_point: Location):
        self.grid = np.array([np.zeros(width)for row in range(height)])
        self.width: int = width
        self.height: int = height
        self.zones: Dict[str, Dict] = zones          # brut (jour 1)
        self.entry_point: Location = entry_point

    def show(self):
        color_map = {
        'A': 0,  # Bleu - electronique
        'B': 1,  # Marron - Livres
        'C': 2,  # Vert - Alimentaire
        'D': 3,  # Rouge - Chimie
        'E': 4,  # Orange - Textile
        '0': 5,  # Blanc - Allee
        '1': 6   # Violet - Entree
        }

        warehouse_colors = [[color_map[cell] for cell in row] for row in self.grid]
        plt.imshow(warehouse_colors, cmap='tab10')
        plt.colorbar()
        plt.show()


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

class Agent:
    def __init__(self, type, id, capacity_weight, capacity_volume, speed, cost_per_hour, restrictions):
        self.type = type
        self.id = id
        self.capacity_weight = capacity_weight
        self.capacity_volume = capacity_volume
        self.speed = speed
        self.cost_per_hour = cost_per_hour
        self.restrictions = restrictions


class Team:
    def __init__(self, agents: list[dict]):

        self.agents = {agent['id'] : Agent(agent['id'], agent['type'], agent['capacity_weight'], agent['capacity_volume'], agent['speed'], agent['cost_per_hour'], agent['restrictions']) for agent in agents}

    def __str__(self):
        return ", ".join(self.agents.keys())


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
        return hash((self.product, self.quantity, self.zone))

    def __repr__(self):
        return f"OrderItem(product_id={self.product}, quantity={self.quantity}"


class Order:
    def __init__(self, id: str, received_time: str, deadline: str, priority: str, items: List[Dict], products: Dict[str, Product]):
        self.id = id
        self.received_time = received_time
        self.deadline = deadline
        self.priority = priority
        self.items = []
        for item in items:
            self.items.append(OrderItem(products[item['product_id']], item['quantity']))

    def __repr__(self):
        return f"Order(id={self.id}, priority={self.priority})"
