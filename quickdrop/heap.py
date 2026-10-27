"""Hand-written binary Min-Heap and a Priority Queue built on top of it.

No ``heapq`` is used. The heap is stored in a plain Python list where, for the
item at index ``i``:

* its parent is at ``(i - 1) // 2``
* its left child is at ``2 * i + 1``
* its right child is at ``2 * i + 2``

The heap property: every parent's key is <= its children's keys, so the
smallest item is always at index 0.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, Iterator, List, Optional, Tuple, TypeVar

T = TypeVar("T")


def _identity(item: Any) -> Any:
    """Default key function: compare items directly. O(1) time, O(1) space."""
    return item


class MinHeap(Generic[T]):
    """Binary min-heap ordered by ``key(item)``.

    Ties (equal keys) are broken by insertion order (FIFO), using a running
    counter, so the heap is *stable* and never has to compare items directly.

    Space: O(n) for n stored items.
    """

    def __init__(self, key: Optional[Callable[[T], Any]] = None,
                 items: Optional[Iterable[T]] = None) -> None:
        """Create a heap, optionally filled with ``items``.

        Time: O(n) when ``items`` is given (bottom-up heapify), else O(1).
        Space: O(n).
        """
        self._key: Callable[[T], Any] = key if key is not None else _identity
        # Each slot holds (key, counter, item); counter breaks ties FIFO.
        self._data: List[Tuple[Any, int, T]] = []
        self._counter: int = 0
        if items is not None:
            for item in items:
                self._data.append((self._key(item), self._counter, item))
                self._counter += 1
            self._heapify()

    # ---------- public API ----------

    def push(self, item: T) -> None:
        """Insert ``item``. Time: O(log n). Space: O(1) extra."""
        self._data.append((self._key(item), self._counter, item))
        self._counter += 1
        self._sift_up(len(self._data) - 1)

    def pop(self) -> T:
        """Remove and return the smallest item.

        Raises IndexError if empty. Time: O(log n). Space: O(1).
        """
        if not self._data:
            raise IndexError("pop from empty heap")
        last = self._data.pop()          # take the last slot off the end
        if not self._data:               # it was the only item
            return last[2]
        top = self._data[0]
        self._data[0] = last             # move last item to the root ...
        self._sift_down(0)               # ... and push it down to its place
        return top[2]

    def peek(self) -> T:
        """Return (not remove) the smallest item. Time: O(1). Space: O(1)."""
        if not self._data:
            raise IndexError("peek from empty heap")
        return self._data[0][2]

    def is_empty(self) -> bool:
        """True if the heap has no items. Time: O(1). Space: O(1)."""
        return not self._data

    def to_sorted_list(self) -> List[T]:
        """Return all items in ascending key order WITHOUT modifying the heap.

        Time: O(n log n). Space: O(n).
        """
        copy: MinHeap[T] = MinHeap(self._key)
        copy._data = list(self._data)
        copy._counter = self._counter
        result: List[T] = []
        while not copy.is_empty():
            result.append(copy.pop())
        return result

    def __len__(self) -> int:
        """Number of items. Time: O(1). Space: O(1)."""
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        """Iterate in *heap array* order (not sorted). Time: O(n). Space: O(1)."""
        return (slot[2] for slot in self._data)

    # ---------- internal helpers ----------

    def _less(self, i: int, j: int) -> bool:
        """True if slot i should be above slot j. Time: O(1). Space: O(1)."""
        a, b = self._data[i], self._data[j]
        return (a[0], a[1]) < (b[0], b[1])

    def _swap(self, i: int, j: int) -> None:
        """Swap two slots. Time: O(1). Space: O(1)."""
        self._data[i], self._data[j] = self._data[j], self._data[i]

    def _sift_up(self, i: int) -> None:
        """Move slot i up while it is smaller than its parent.

        Time: O(log n) - at most the height of the tree. Space: O(1).
        """
        while i > 0:
            parent = (i - 1) // 2
            if self._less(i, parent):
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        """Move slot i down while a child is smaller than it.

        Time: O(log n). Space: O(1).
        """
        n = len(self._data)
        while True:
            left, right = 2 * i + 1, 2 * i + 2
            smallest = i
            if left < n and self._less(left, smallest):
                smallest = left
            if right < n and self._less(right, smallest):
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    def _heapify(self) -> None:
        """Bottom-up heap construction (Floyd's method).

        Time: O(n) - most nodes are near the bottom and sift only a little.
        Space: O(1).
        """
        for i in range(len(self._data) // 2 - 1, -1, -1):
            self._sift_down(i)


class PriorityQueue(Generic[T]):
    """Priority queue: the item with the *smallest* priority key comes out first.

    A thin wrapper over :class:`MinHeap` with queue-style method names.
    Example - VIP first, then oldest first::

        pq = PriorityQueue(key=lambda o: (0 if o.vip else 1, o.created_at))

    Space: O(n).
    """

    def __init__(self, key: Optional[Callable[[T], Any]] = None) -> None:
        """Create an empty priority queue. Time: O(1). Space: O(1)."""
        self._heap: MinHeap[T] = MinHeap(key)

    def enqueue(self, item: T) -> None:
        """Add an item. Time: O(log n). Space: O(1)."""
        self._heap.push(item)

    def dequeue(self) -> T:
        """Remove and return the highest-priority item. Time: O(log n). Space: O(1)."""
        return self._heap.pop()

    def peek(self) -> T:
        """Return the highest-priority item without removing it. Time: O(1)."""
        return self._heap.peek()

    def is_empty(self) -> bool:
        """True if empty. Time: O(1). Space: O(1)."""
        return self._heap.is_empty()

    def snapshot(self) -> List[T]:
        """Items in priority order, queue unchanged. Time: O(n log n). Space: O(n)."""
        return self._heap.to_sorted_list()

    def __len__(self) -> int:
        """Number of items. Time: O(1). Space: O(1)."""
        return len(self._heap)
