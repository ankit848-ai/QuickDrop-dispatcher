"""Tests for quickdrop.dispatcher and quickdrop.strategies."""

import pytest

from quickdrop.dispatcher import Dispatcher, waiting_priority
from quickdrop.models import Order, Restaurant, Rider
from quickdrop.strategies import get_strategy, greedy_heap, naive_first


def make_riders() -> list:
    # Rider 0 far away, rider 1 close, rider 2 closest but busy.
    riders = [Rider(0, 40, 40), Rider(1, 6, 5), Rider(2, 5, 5, is_free=False)]
    return riders


def test_greedy_picks_nearest_free() -> None:
    riders = make_riders()
    free = [r for r in riders if r.is_free]
    assert greedy_heap(riders, free, (5, 5)).id == 1


def test_naive_picks_first_free_by_id() -> None:
    riders = make_riders()
    free = [r for r in riders if r.is_free]
    assert naive_first(riders, free, (5, 5)).id == 0


def test_strategies_return_none_when_all_busy() -> None:
    riders = [Rider(0, 0, 0, is_free=False)]
    assert greedy_heap(riders, [], (1, 1)) is None
    assert naive_first(riders, [], (1, 1)) is None


def test_get_strategy_unknown() -> None:
    assert get_strategy("greedy") is greedy_heap
    with pytest.raises(ValueError):
        get_strategy("random")


def test_greedy_tie_breaks_by_lower_id() -> None:
    riders = [Rider(3, 4, 5), Rider(1, 6, 5)]  # both distance 1 from (5,5)
    assert greedy_heap(riders, riders, (5, 5)).id == 3  # first inserted wins


def test_assign_marks_rider_busy() -> None:
    d = Dispatcher([Rider(0, 0, 0)], [Restaurant(0, "R", 1, 1)])
    o = Order(0, 0, 3, 3, created_at=5)
    rider = d.assign_order(o, now=5)
    assert rider is not None and rider.id == 0
    assert not rider.is_free and rider.current_order == 0
    assert o.rider_id == 0 and o.assigned_at == 5
    assert 0 not in d.free


def test_order_waits_when_no_rider_then_vip_first() -> None:
    d = Dispatcher([Rider(0, 0, 0)], [Restaurant(0, "R", 1, 1)])
    first = Order(0, 0, 3, 3, created_at=0)
    d.assign_order(first, 0)                       # takes the only rider
    normal_old = Order(1, 0, 2, 2, created_at=1)
    vip_new = Order(2, 0, 2, 2, created_at=2, vip=True)
    normal_new = Order(3, 0, 2, 2, created_at=3)
    for o in (normal_old, vip_new, normal_new):
        assert d.assign_order(o, o.created_at) is None
    assert [o.id for o in d.waiting_snapshot()] == [2, 1, 3]

    rider = d.riders[0]
    nxt = d.complete_delivery(rider, first, now=10)
    assert nxt is vip_new                          # VIP jumps the queue
    assert first.delivered_at == 10 and rider.deliveries == 1
    assert rider.pos == (3, 3)                     # freed at customer location
    assert not rider.is_free and vip_new.assigned_at == 10
    assert len(d.waiting) == 2


def test_complete_with_empty_queue_frees_rider() -> None:
    d = Dispatcher([Rider(0, 0, 0)], [Restaurant(0, "R", 1, 1)])
    o = Order(0, 0, 3, 3, created_at=0)
    rider = d.assign_order(o, 0)
    assert d.complete_delivery(rider, o, 7) is None
    assert rider.is_free and 0 in d.free


def test_waiting_priority_key() -> None:
    assert waiting_priority(Order(5, 0, 0, 0, 9, vip=True)) < waiting_priority(Order(1, 0, 0, 0, 1))
