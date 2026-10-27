"""Tests for quickdrop.heap (MinHeap and PriorityQueue)."""

import random

import pytest

from quickdrop.heap import MinHeap, PriorityQueue


def test_push_pop_returns_sorted_order() -> None:
    nums = [5, 3, 8, 1, 9, 2, 7]
    heap: MinHeap[int] = MinHeap()
    for n in nums:
        heap.push(n)
    assert [heap.pop() for _ in nums] == sorted(nums)
    assert heap.is_empty()


def test_heapify_constructor_matches_sorted() -> None:
    rng = random.Random(42)
    nums = [rng.randint(-1000, 1000) for _ in range(500)]
    heap = MinHeap(items=nums)
    assert len(heap) == 500
    assert [heap.pop() for _ in range(500)] == sorted(nums)


def test_peek_does_not_remove() -> None:
    heap = MinHeap(items=[4, 2, 6])
    assert heap.peek() == 2
    assert len(heap) == 3


def test_empty_pop_and_peek_raise() -> None:
    heap: MinHeap[int] = MinHeap()
    with pytest.raises(IndexError):
        heap.pop()
    with pytest.raises(IndexError):
        heap.peek()


def test_key_function_and_stable_ties() -> None:
    # Same key -> insertion order must be kept (FIFO).
    heap: MinHeap[tuple] = MinHeap(key=lambda t: t[0])
    for item in [(2, "a"), (1, "b"), (2, "c"), (1, "d")]:
        heap.push(item)
    assert [heap.pop()[1] for _ in range(4)] == ["b", "d", "a", "c"]


def test_items_without_ordering_work_with_key() -> None:
    class Thing:  # not comparable on its own
        def __init__(self, v: int) -> None:
            self.v = v

    heap: MinHeap[Thing] = MinHeap(key=lambda t: t.v)
    for v in [3, 1, 2]:
        heap.push(Thing(v))
    assert [heap.pop().v for _ in range(3)] == [1, 2, 3]


def test_to_sorted_list_leaves_heap_intact() -> None:
    heap = MinHeap(items=[3, 1, 2])
    assert heap.to_sorted_list() == [1, 2, 3]
    assert len(heap) == 3
    assert heap.pop() == 1


def test_priority_queue_vip_then_oldest() -> None:
    # (id, vip, created_at)
    orders = [(1, False, 0), (2, True, 5), (3, False, 1), (4, True, 2)]
    pq = PriorityQueue(key=lambda o: (0 if o[1] else 1, o[2]))
    for o in orders:
        pq.enqueue(o)
    assert [o[0] for o in pq.snapshot()] == [4, 2, 1, 3]
    assert pq.peek()[0] == 4
    assert [pq.dequeue()[0] for _ in range(4)] == [4, 2, 1, 3]
    assert pq.is_empty() and len(pq) == 0


def test_random_interleaved_operations() -> None:
    rng = random.Random(7)
    heap: MinHeap[int] = MinHeap()
    reference: list = []
    for _ in range(2000):
        if reference and rng.random() < 0.4:
            reference.sort()
            assert heap.pop() == reference.pop(0)
        else:
            v = rng.randint(0, 100)
            heap.push(v)
            reference.append(v)
    assert len(heap) == len(reference)
