"""Hand-written FIFO Queue backed by a singly linked list.

Used by BFS in ``city.py``. We keep pointers to both the ``head`` (front, where
we dequeue) and the ``tail`` (back, where we enqueue) so both operations are
O(1). A Python list's ``pop(0)`` would be O(n), which is why we don't use it.
"""

from __future__ import annotations

from typing import Generic, Iterator, Optional, TypeVar

T = TypeVar("T")


class _Node(Generic[T]):
    """One link in the chain: a value plus a pointer to the next node.

    Time: O(1) to create. Space: O(1).
    """

    __slots__ = ("value", "next")

    def __init__(self, value: T) -> None:
        """Create a node holding ``value``. Time: O(1). Space: O(1)."""
        self.value: T = value
        self.next: Optional[_Node[T]] = None


class Queue(Generic[T]):
    """First-In-First-Out queue.

    head -> [a] -> [b] -> [c] <- tail
    dequeue() takes from head, enqueue() adds after tail.

    Space: O(n) for n items.
    """

    def __init__(self) -> None:
        """Create an empty queue. Time: O(1). Space: O(1)."""
        self._head: Optional[_Node[T]] = None
        self._tail: Optional[_Node[T]] = None
        self._size: int = 0

    def enqueue(self, value: T) -> None:
        """Add ``value`` at the back. Time: O(1). Space: O(1)."""
        node = _Node(value)
        if self._tail is None:          # empty queue: node is head and tail
            self._head = self._tail = node
        else:
            self._tail.next = node
            self._tail = node
        self._size += 1

    def dequeue(self) -> T:
        """Remove and return the front value.

        Raises IndexError if empty. Time: O(1). Space: O(1).
        """
        if self._head is None:
            raise IndexError("dequeue from empty queue")
        node = self._head
        self._head = node.next
        if self._head is None:          # queue became empty
            self._tail = None
        self._size -= 1
        return node.value

    def peek(self) -> T:
        """Return the front value without removing it. Time: O(1). Space: O(1)."""
        if self._head is None:
            raise IndexError("peek from empty queue")
        return self._head.value

    def is_empty(self) -> bool:
        """True if the queue has no items. Time: O(1). Space: O(1)."""
        return self._size == 0

    def __len__(self) -> int:
        """Number of items. Time: O(1). Space: O(1)."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Iterate front to back without removing. Time: O(n). Space: O(1)."""
        node = self._head
        while node is not None:
            yield node.value
            node = node.next
