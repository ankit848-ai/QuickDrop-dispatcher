"""Event-driven simulation of a day of deliveries.

Instead of ticking a clock minute by minute, we keep a Min-Heap of future
events ordered by timestamp and always jump straight to the next one:

* ORDER  - a customer places an order       -> dispatcher.assign_order()
* DONE   - a rider reaches the customer     -> dispatcher.complete_delivery()

When a rider is assigned we compute the full BFS route
(rider -> restaurant -> customer); its length in cells is the trip time in
minutes, so we can schedule the DONE event right away.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .city import City
from .dispatcher import Dispatcher
from .heap import MinHeap
from .metrics import compute_metrics
from .models import Order, Restaurant, Rider

DONE = 0    # processed before ORDER at the same minute, so freed riders count
ORDER = 1


@dataclass
class Event:
    """Something that happens at minute ``time``. Space: O(1)."""

    time: int
    kind: int                 # DONE or ORDER
    order_id: int
    rider_id: Optional[int] = None


@dataclass
class SimulationResult:
    """Everything a run produced. Space: O(N + R + F) for F frames."""

    orders: List[Order]
    riders: List[Rider]
    metrics: Dict[str, float]
    frames: List[Dict[str, Any]] = field(default_factory=list)
    events_processed: int = 0
    runtime_ms: float = 0.0


class Simulator:
    """Runs the event loop.

    Total time: O(N log N + N*(D + L)) where N = orders, D = cost of one
    dispatch decision (O(F) greedy / O(R) naive) and L = route length.
    BFS trees are cached per restaurant, so each route is O(L) after the
    first BFS from that restaurant (O(W*H)).
    Space: O(N + R + W*H * restaurants).
    """

    def __init__(self, city: City, restaurants: List[Restaurant], riders: List[Rider],
                 orders: List[Order], strategy: str = "greedy",
                 frame_every: Optional[int] = None, frame_queue_limit: int = 15) -> None:
        """Prepare a run. ``frame_every`` (minutes) turns on animation frames.

        Time: O(N + R). Space: O(N + R).
        """
        self.city = city
        self.riders = riders
        self.orders = orders
        self.orders_by_id: Dict[int, Order] = {o.id: o for o in orders}
        self.restaurants: Dict[int, Restaurant] = {r.id: r for r in restaurants}
        self.dispatcher = Dispatcher(riders, restaurants, strategy)
        self.frame_every = frame_every
        self.frame_queue_limit = frame_queue_limit
        self.frames: List[Dict[str, Any]] = []
        self._next_frame: Optional[int] = None
        self._delivered = 0
        # Events with the same time: DONE before ORDER, then FIFO.
        self.events: MinHeap[Event] = MinHeap(
            key=lambda e: (e.time, e.kind),
            items=[Event(o.created_at, ORDER, o.id) for o in orders],
        )

    def run(self) -> SimulationResult:
        """Process events until none are left. Time/Space: see class docstring."""
        started = time.perf_counter()
        processed = 0
        now = 0
        if self.frame_every and self.orders:
            self._next_frame = min(o.created_at for o in self.orders)

        while not self.events.is_empty():
            event = self.events.pop()
            self._frames_before(event.time)     # snapshot the state up to now
            now = event.time
            processed += 1
            order = self.orders_by_id[event.order_id]
            if event.kind == ORDER:
                rider = self.dispatcher.assign_order(order, now)
                if rider is not None:
                    self._start_trip(rider, order, now)
            else:
                rider = self.dispatcher.riders[event.rider_id]
                self._delivered += 1
                next_order = self.dispatcher.complete_delivery(rider, order, now)
                if next_order is not None:
                    self._start_trip(rider, next_order, now)

        if self.frame_every:
            self._record_frame(now)             # final state
        runtime_ms = (time.perf_counter() - started) * 1000
        return SimulationResult(
            orders=self.orders,
            riders=self.riders,
            metrics=compute_metrics(self.orders, self.riders),
            frames=self.frames,
            events_processed=processed,
            runtime_ms=round(runtime_ms, 3),
        )

    # ---------- helpers ----------

    def _start_trip(self, rider: Rider, order: Order, now: int) -> None:
        """Compute rider -> restaurant -> customer route and schedule DONE.

        Both legs come from ONE cached BFS tree rooted at the restaurant
        (the grid is undirected, so restaurant->rider reversed = rider->restaurant).
        Time: O(L) (+ O(W*H) the first time a restaurant is used). Space: O(L).
        """
        rest = self.restaurants[order.restaurant_id].pos
        to_rider = self.city.path_from(rest, rider.pos)
        to_customer = self.city.path_from(rest, order.customer_pos)
        if to_rider is None or to_customer is None:
            raise ValueError(f"order {order.id}: no route on this map")
        to_rider.reverse()                      # now rider -> restaurant
        order.path = to_rider + to_customer[1:]
        trip = len(order.path) - 1
        order.picked_up_at = now + len(to_rider) - 1
        rider.busy_time += trip
        self.events.push(Event(now + trip, DONE, order.id, rider.id))

    def _frames_before(self, t: int) -> None:
        """Record every frame whose time is strictly before ``t``.

        Time: O(frames * (R + Q log Q)). Space: O(R) per frame.
        """
        while self._next_frame is not None and self._next_frame < t:
            self._record_frame(self._next_frame)
            self._next_frame += self.frame_every  # type: ignore[operator]

    def _record_frame(self, t: int) -> None:
        """Snapshot rider positions/states and the waiting queue at minute t.

        A busy rider's position is ``path[t - assigned_at]``.
        Time: O(R + W log W). Space: O(R + K) for K shown queue entries.
        """
        riders = []
        for r in self.riders:
            if r.is_free:
                riders.append([r.x, r.y, 0, -1])
            else:
                o = self.orders_by_id[r.current_order]          # type: ignore[index]
                step = min(max(0, t - o.assigned_at), len(o.path) - 1)  # type: ignore[operator]
                x, y = o.path[step]
                riders.append([x, y, 1, o.id])
        waiting = self.dispatcher.waiting_snapshot()
        self.frames.append({
            "t": t,
            "riders": riders,
            "waiting": [[o.id, int(o.vip), o.created_at] for o in waiting[: self.frame_queue_limit]],
            "waiting_count": len(waiting),
            "delivered": self._delivered,
        })


def simulate(city: City, restaurants: List[Restaurant], riders: List[Rider],
             orders: List[Order], strategy: str = "greedy",
             frame_every: Optional[int] = None) -> SimulationResult:
    """Convenience wrapper: build a Simulator and run it. Time/Space: see Simulator."""
    return Simulator(city, restaurants, riders, orders, strategy, frame_every).run()
