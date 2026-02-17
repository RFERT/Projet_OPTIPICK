from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Location:
    x: int
    y: int

    @classmethod
    def from_list(cls, coords: List[int]) -> "Location":
        return cls(coords[0], coords[1])


@dataclass
class Warehouse:
    width: int
    height: int
    zones: Dict[str, Dict]
    entry_point: Location
    aisles: List[Location] = field(default_factory=list)


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

    @classmethod
    def from_dict(cls, data: Dict) -> "Agent":
        return cls(
            id=data["id"],
            type=data["type"],
            capacity_weight=data["capacity_weight"],
            capacity_volume=data["capacity_volume"],
            speed=data["speed"],
            cost_per_hour=data["cost_per_hour"],
            restrictions=data.get("restrictions", {}),
        )


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
