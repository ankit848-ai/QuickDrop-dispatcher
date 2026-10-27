"""Two ways of picking a rider for an order.

(a) ``greedy_heap``   - build a Min-Heap of FREE riders keyed by Manhattan
                        distance to the restaurant and pop the nearest one.
(b) ``naive_first``   - scan ALL riders in id order and take the first one
                        that happens to be free, ignoring distance.

Both return ``None`` when no rider is free.
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional

from .city import manhattan
from .heap import MinHeap
from .models import Point, Rider

# A strategy gets (all riders, free riders, restaurant position) -> chosen rider.
Strategy = Callable[[Iterable[Rider], Iterable[Rider], Point], Optional[Rider]]


def greedy_heap(all_riders: Iterable[Rider], free_riders: Iterable[Rider],
                restaurant: Point) -> Optional[Rider]:
    """Nearest free rider by Manhattan distance, using our MinHeap.

    Heapify the F free riders (O(F)), then pop the minimum (O(log F)).
    Ties on distance go to the rider inserted first (lower id), so results
    are deterministic.
    Time: O(F). Space: O(F).
    """
    heap: MinHeap[Rider] = MinHeap(key=lambda r: manhattan(r.pos, restaurant),
                                   items=free_riders)
    if heap.is_empty():
        return None
    return heap.pop()


def naive_first(all_riders: Iterable[Rider], free_riders: Iterable[Rider],
                restaurant: Point) -> Optional[Rider]:
    """First free rider found by a linear scan over every rider.

    Time: O(R) for R riders in total. Space: O(1).
    """
    for rider in all_riders:
        if rider.is_free:
            return rider
    return None


STRATEGIES: Dict[str, Strategy] = {
    "greedy": greedy_heap,
    "naive": naive_first,
}


def get_strategy(name: str) -> Strategy:
    """Look up a strategy by name ('greedy' or 'naive'). Time: O(1). Space: O(1)."""
    if name not in STRATEGIES:
        raise ValueError(f"unknown strategy {name!r}; choose from {sorted(STRATEGIES)}")
    return STRATEGIES[name]
