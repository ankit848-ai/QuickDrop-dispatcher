"""Tests for the data generator, simulator and metrics."""

import csv
import os

from data.generate_data import generate_scenario, save_csv
from quickdrop.city import City, manhattan
from quickdrop.metrics import compute_metrics
from quickdrop.models import Order, Restaurant, Rider
from quickdrop.simulator import simulate


def test_generator_is_reproducible_and_valid() -> None:
    a = generate_scenario(riders=10, orders=200, city_size=30, seed=5)
    b = generate_scenario(riders=10, orders=200, city_size=30, seed=5)
    assert [(o.created_at, o.customer_pos, o.vip) for o in a.orders] == \
           [(o.created_at, o.customer_pos, o.vip) for o in b.orders]
    times = [o.created_at for o in a.orders]
    assert times == sorted(times)
    for o in a.orders:
        assert a.city.is_free(o.customer_pos)
    for r in a.riders + a.restaurants:
        assert a.city.is_free(r.pos)
    vip = sum(o.vip for o in a.orders) / len(a.orders)
    assert 0.03 < vip < 0.2


def test_generator_has_lunch_and_dinner_peaks() -> None:
    s = generate_scenario(riders=5, orders=2000, city_size=20, seed=1)
    lunch = sum(1 for o in s.orders if 11 * 60 <= o.created_at < 14 * 60)
    afternoon = sum(1 for o in s.orders if 15 * 60 <= o.created_at < 18 * 60)
    dinner = sum(1 for o in s.orders if 19 * 60 <= o.created_at < 22 * 60)
    assert lunch > 3 * afternoon and dinner > 3 * afternoon


def test_save_csv(tmp_path) -> None:
    s = generate_scenario(riders=3, orders=10, city_size=15, seed=2)
    paths = save_csv(s, str(tmp_path))
    assert len(paths) == 4
    with open(os.path.join(tmp_path, "orders.csv"), newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "id" and len(rows) == 11


def test_all_orders_delivered_with_consistent_times() -> None:
    s = generate_scenario(riders=8, orders=150, city_size=25, seed=9)
    result = simulate(s.city, s.restaurants, s.riders, s.orders, "greedy")
    assert result.metrics["delivered"] == 150
    assert result.events_processed == 300            # one ORDER + one DONE each
    for o in result.orders:
        assert o.created_at <= o.assigned_at <= o.picked_up_at <= o.delivered_at
        assert o.delivered_at - o.assigned_at == len(o.path) - 1
        assert o.path[-1] == o.customer_pos
        for a, b in zip(o.path, o.path[1:]):         # contiguous, obstacle-free
            assert manhattan(a, b) == 1 and s.city.is_free(b)
    assert all(r.is_free for r in result.riders)


def test_single_rider_hand_checked_timeline() -> None:
    city = City(10, 10)
    rest = [Restaurant(0, "R", 5, 0)]
    riders = [Rider(0, 0, 0)]
    orders = [Order(0, 0, 5, 5, created_at=0), Order(1, 0, 9, 0, created_at=1, vip=True),
              Order(2, 0, 0, 0, created_at=2)]
    result = simulate(city, rest, riders, orders)
    o0, o1, o2 = result.orders
    # Order 0: rider 0,0 -> 5,0 (5) -> 5,5 (5) = done at 10.
    assert (o0.assigned_at, o0.picked_up_at, o0.delivered_at) == (0, 5, 10)
    # VIP order 1 is served before order 2 even though both wait.
    assert o1.assigned_at == 10 and o1.delivered_at == 10 + 5 + 4
    assert o2.assigned_at == o1.delivered_at
    assert o1.wait_time == 9 and o2.wait_time == 17   # VIP waited less


def test_greedy_beats_naive_on_delivery_time() -> None:
    kwargs = dict(riders=30, orders=400, city_size=40, seed=3)
    g = generate_scenario(**kwargs)
    n = generate_scenario(**kwargs)
    rg = simulate(g.city, g.restaurants, g.riders, g.orders, "greedy")
    rn = simulate(n.city, n.restaurants, n.riders, n.orders, "naive")
    assert rg.metrics["avg_delivery_time"] < rn.metrics["avg_delivery_time"]


def test_frames_recorded() -> None:
    s = generate_scenario(riders=5, orders=50, city_size=20, seed=4)
    result = simulate(s.city, s.restaurants, s.riders, s.orders, frame_every=10)
    frames = result.frames
    assert len(frames) > 5
    assert all(len(f["riders"]) == 5 for f in frames)
    assert [f["t"] for f in frames] == sorted(f["t"] for f in frames)
    assert frames[-1]["delivered"] == 50 and frames[-1]["waiting_count"] == 0
    for f in frames:
        for x, y, busy, oid in f["riders"]:
            assert s.city.is_free((x, y))
            assert (busy == 1) == (oid != -1)


def test_metrics_values() -> None:
    riders = [Rider(0, 0, 0, busy_time=30), Rider(1, 0, 0, busy_time=10)]
    o1 = Order(0, 0, 0, 0, created_at=0, vip=True)
    o1.assigned_at, o1.delivered_at = 0, 20
    o2 = Order(1, 0, 0, 0, created_at=10)
    o2.assigned_at, o2.delivered_at = 20, 40
    m = compute_metrics([o1, o2], riders)
    assert m["avg_delivery_time"] == 25
    assert m["avg_wait_time"] == 5
    assert m["utilization"] == round(40 / (2 * 40), 4)
    assert m["orders_per_hour"] == 3.0
    assert compute_metrics([], [])["delivered"] == 0
