"""Tests for quickdrop.linked_queue.Queue."""

import pytest

from quickdrop.linked_queue import Queue


def test_fifo_order() -> None:
    q: Queue[int] = Queue()
    for i in range(5):
        q.enqueue(i)
    assert len(q) == 5
    assert [q.dequeue() for _ in range(5)] == [0, 1, 2, 3, 4]
    assert q.is_empty()


def test_peek_and_iter() -> None:
    q: Queue[str] = Queue()
    q.enqueue("a")
    q.enqueue("b")
    assert q.peek() == "a"
    assert list(q) == ["a", "b"]
    assert len(q) == 2


def test_empty_raises() -> None:
    q: Queue[int] = Queue()
    with pytest.raises(IndexError):
        q.dequeue()
    with pytest.raises(IndexError):
        q.peek()


def test_reuse_after_emptying() -> None:
    # Tail pointer must be reset when the queue empties.
    q: Queue[int] = Queue()
    q.enqueue(1)
    q.dequeue()
    q.enqueue(2)
    q.enqueue(3)
    assert list(q) == [2, 3]
    assert q.dequeue() == 2
