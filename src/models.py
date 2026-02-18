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


class Agent:
    # id: str
    # type: str  # "robot" | "human" | "cart"

    def __init__(self, type, id):
        if type == "robot":
            self.restrictions = {"Zone" : "C", "fragile" : True, "weight" : 10, "agent" : None}
            self.capacity_weight, self.capacity_volume = 20, 30
            self.speed = 2.0
            self.cost_per_hour = 5
            self.id = id
            self.type = type
        elif type == "human":
            self.restrictions = {"Zone" : None, "fragile" : None, "weight" : None, "agent" : None}
            self.capacity_weight, self.capacity_volume = 35, 50
            self.speed = 1.5
            self.cost_per_hour = 25
            self.id = id
            self.type = type
        elif type == "cart":
            self.restrictions = {"Zone" : None, "fragile" : None, "weight" : None, "agent" : "human"}
            self.capacity_weight, self.capacity_volume = 50, 80
            self.speed = 1.2
            self.cost_per_hour = 3
            self.id = id
            self.type = type
        else:
            raise TypeError


class Team:
    def __init__(self):
        self.limits = {"robot" : 3, "human" : 2, "cart" : 2}

        self.agents = {"R1": Agent("robot", "R1"), "R2": Agent("robot", "R2"), "R3": Agent("robot", "R3"),
                       "H1": Agent("human", "H1"), "H2": Agent("human", "H2"),
                        "C1": Agent("cart", "C1"), "C2": Agent("cart", "C2")}
    
    def __str__(self):
        return ", ".join(self.agents.keys())


class OrderItem:
    def __init__(self, product_id: str, quantity: int, zone: str = None):
        self.product_id = product_id
        self.quantity = quantity
        self.zone = zone

    def __eq__(self, other):
        if isinstance(other, OrderItem):
            return (self.product_id == other.product_id and 
                    self.quantity == other.quantity and 
                    self.zone == other.zone)
        return False

    def __hash__(self):
        return hash((self.product_id, self.quantity, self.zone))

    def __repr__(self):
        return f"OrderItem(product_id={self.product_id}, quantity={self.quantity}, zone={self.zone})"


class Order:
    def __init__(self, id: str, received_time: str, deadline: str, priority: str, items: List[OrderItem]):
        self.id = id
        self.received_time = received_time
        self.deadline = deadline
        self.priority = priority
        self.items = items

    def __repr__(self):
        return f"Order(id={self.id}, priority={self.priority})"
