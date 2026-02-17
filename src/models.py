from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from random import randint
import matplotlib.pyplot as plt
import numpy as np

@dataclass(frozen=True)
class Location:
    x: int
    y: int



class Warehouse:
    def __init__(self):
        self.grid = np.array([np.zeros(width)for row in range(height)])
        width: int
        height: int
        zones: Dict[str, Dict]          # brut (jour 1)
        entry_point: Location

    def show(self):
        color_map = {
        'A': 0,  # Bleu - Électronique
        'B': 1,  # Marron - Livres
        'C': 2,  # Vert - Alimentaire
        'D': 3,  # Rouge - Chimie
        'E': 4,  # Orange - Textile
        '0': 5,  # Blanc - Allée
        '1': 6   # Violet - Entrée
        }

        warehouse_colors = [[color_map[cell] for cell in row] for row in self.grid]
        plt.imshow(warehouse_colors, cmap='tab10')
        plt.colorbar()
        plt.show()

@dataclass
class Product:
    id: str
    name: str
    category: str
    weight: float
    volume: float
    location: Location
    frequency: str
    fragile: bool
    incompatible_with: List[str] = field(default_factory=list)

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
        elif type == "human":
            self.restrictions = {"Zone" : None, "fragile" : None, "weight" : None, "agent" : None}
            self.capacity_weight, self.capacity_volume = 35, 50
            self.speed = 1.5
            self.cost_per_hour = 25
            self.id = id
        elif type == "cart":
            self.restrictions = {"Zone" : None, "fragile" : None, "weight" : None, "agent" : "human"}
            self.capacity_weight, self.capacity_volume = 50, 80
            self.speed = 1.2
            self.cost_per_hour = 3
            self.id = id
        else:
            raise TypeError

class Team:
    def __init__(self):
        self.limits = {"robot" : 3, "human" : 2, "cart" : 2}

        self.agents = {"R1": Agent("robot", "R1"), "R2": Agent("robot", "R2"), "R3": Agent("robot", "R3"),\
                       "H1": Agent("human", "H1"), "H2": Agent("human", "H2"), \
                        "C1": Agent("cart", "C1"), "C2": Agent("cart", "C2")}
    
    def __str__(self):
        return ", ".join(self.agents.keys())

@dataclass(frozen=True)
class OrderItem:
    product_id: str
    quantity: int
    zone: str

@dataclass
class Order:
    id: str
    received_time: str
    deadline: str
    priority: str
    items: List[OrderItem]
