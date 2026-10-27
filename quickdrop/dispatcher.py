"""The dispatcher: decides which rider gets which order.

State it keeps:

* ``riders``      - hash map id -> Rider (all riders), O(1) lookup.
* ``free``        - hash map id -> Rider (only free riders), O(1) add/remove.
* ``waiting``     - PriorityQueue of orders with no rider yet:
                    VIP first, then older orders first, then lower id.

The dispatcher does not know about time passing or routes; the simulator
calls it when an order arrives and when a delivery finishes.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .heap import PriorityQueue
from .models import Order, Restaurant, Rider
from .strategies import Strategy, get_strategy


def waiting_priority(order: Order) -> Tuple[int, int, int]:
    """Priority key for the waiting queue: smaller = served first.

    (0 for VIP / 1 for normal, creation time, id).
    Time: O(1). Space: O(1).
    """
    return (0 if order.vip else 1, order.created_at, order.id)


class Dispatcher:
    """Assigns orders to riders using a pluggable strategy.

    Space: O(R + W) for R riders and W waiting orders.
    """

    def __init__(self, riders: List[Rider], restaurants: List[Restaurant],
                 strategy: str = "greedy") -> None:
        """Set up the hash maps and waiting queue. Time: O(R + N). Space: O(R + N)."""
        self.riders: Dict[int, Rider] = {r.id: r for r in riders}
        self.free: Dict[int, Rider] = {r.id: r for r in riders if r.is_free}
        self.restaurants: Dict[int, Restaurant] = {r.id: r for r in restaurants}
        self.waiting: PriorityQueue[Order] = PriorityQueue(key=waiting_priority)
        self.strategy_name: str = strategy
        self._strategy: Strategy = get_strategy(strategy)

    def assign_order(self, order: Order, now: int) -> Optional[Rider]:
        """Try to give ``order`` to a free rider chosen by the strategy.

        If nobody is free the order goes into the waiting priority queue and
        None is returned.
        Time: O(F) for greedy / O(R) for naive, plus O(log W) if it waits.
        Space: O(F) for greedy's temporary heap.
        """
        restaurant = self.restaurants[order.restaurant_id]
        rider = self._strategy(self.riders.values(), self.free.values(), restaurant.pos)
        if rider is None:
            self.waiting.enqueue(order)
            return None
        self._give(rider, order, now)
        return rider

    def complete_delivery(self, rider: Rider, order: Order, now: int) -> Optional[Order]:
        """Rider finished ``order``: they are now free at the customer's cell.

        If orders are waiting, this rider immediately takes the
        highest-priority one, which is returned (else None).
        Time: O(log W). Space: O(1).
        """
        rider.x, rider.y = order.customer_pos
        rider.is_free = True
        rider.current_order = None
        rider.deliveries += 1
        order.delivered_at = now
        if self.waiting.is_empty():
            self.free[rider.id] = rider
            return None
        next_order = self.waiting.dequeue()
        self._give(rider, next_order, now)
        return next_order

    def waiting_snapshot(self) -> List[Order]:
        """Waiting orders in the order they will be served.

        Time: O(W log W). Space: O(W).
        """
        return self.waiting.snapshot()

    def _give(self, rider: Rider, order: Order, now: int) -> None:
        """Mark rider busy with order. Time: O(1). Space: O(1)."""
        rider.is_free = False
        rider.current_order = order.id
        self.free.pop(rider.id, None)
        order.rider_id = rider.id
        order.assigned_at = now
