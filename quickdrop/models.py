"""Plain data classes for the things that live in the city.

Time is measured in whole minutes from the start of the day, and a rider moves
one grid cell per minute, so "distance in cells" == "travel time in minutes".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

Point = Tuple[int, int]


@dataclass
class Restaurant:
    """A restaurant at grid cell (x, y). Space: O(1)."""

    id: int
    name: str
    x: int
    y: int

    @property
    def pos(self) -> Point:
        """(x, y) tuple. Time: O(1). Space: O(1)."""
        return (self.x, self.y)


@dataclass
class Rider:
    """A delivery rider.

    ``is_free`` is True when the rider can take a new order. While busy,
    ``current_order`` holds the id of the order being delivered.
    ``busy_time`` accumulates minutes spent delivering (for utilization).
    Space: O(1).
    """

    id: int
    x: int
    y: int
    is_free: bool = True
    current_order: Optional[int] = None
    deliveries: int = 0
    busy_time: int = 0

    @property
    def pos(self) -> Point:
        """(x, y) tuple. Time: O(1). Space: O(1)."""
        return (self.x, self.y)


@dataclass
class Order:
    """A customer's food order.

    Lifecycle: created_at -> assigned_at (rider chosen) -> picked_up_at
    (rider reaches restaurant) -> delivered_at (rider reaches customer).
    ``path`` is the full grid route the rider follows, from where the rider
    was when assigned, through the restaurant, to the customer.
    Space: O(L) where L = len(path).
    """

    id: int
    restaurant_id: int
    customer_x: int
    customer_y: int
    created_at: int
    vip: bool = False
    rider_id: Optional[int] = None
    assigned_at: Optional[int] = None
    picked_up_at: Optional[int] = None
    delivered_at: Optional[int] = None
    path: List[Point] = field(default_factory=list)

    @property
    def customer_pos(self) -> Point:
        """(x, y) of the customer. Time: O(1). Space: O(1)."""
        return (self.customer_x, self.customer_y)

    @property
    def wait_time(self) -> Optional[int]:
        """Minutes from order placed until a rider was assigned. Time: O(1)."""
        if self.assigned_at is None:
            return None
        return self.assigned_at - self.created_at

    @property
    def delivery_time(self) -> Optional[int]:
        """Minutes from order placed until food delivered. Time: O(1)."""
        if self.delivered_at is None:
            return None
        return self.delivered_at - self.created_at

    @property
    def status(self) -> str:
        """'waiting', 'assigned', or 'delivered'. Time: O(1). Space: O(1)."""
        if self.delivered_at is not None:
            return "delivered"
        if self.assigned_at is not None:
            return "assigned"
        return "waiting"
