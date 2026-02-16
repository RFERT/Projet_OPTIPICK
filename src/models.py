from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Location:
    x: int
    y: int


@dataclass
class Warehouse:
    width: int
    height: int
    zones: Dict[str, Dict]          # brut (jour 1)
    entry_point: Location


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


@dataclass
class Agent:
    id: str
    type: str  # "robot" | "human" | "cart"
    capacity_weight: float
    capacity_volume: float
    speed: float
    cost_per_hour: float
    restrictions: Dict


@dataclass
class Robot(Agent):
    pass


@dataclass
class Human(Agent):
    pass


@dataclass
class Cart(Agent):
    pass


@dataclass(frozen=True)
class OrderItem:
    product_id: str
    quantity: int


@dataclass
class Order:
    id: str
    received_time: str
    deadline: str
    priority: str
    items: List[OrderItem]
