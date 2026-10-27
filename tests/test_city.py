"""Tests for quickdrop.city and quickdrop.models."""

import random

from quickdrop.city import City, manhattan
from quickdrop.models import Order, Restaurant, Rider


def test_manhattan() -> None:
    assert manhattan((0, 0), (3, 4)) == 7
    assert manhattan((5, 5), (5, 5)) == 0
    assert manhattan((2, 9), (7, 1)) == 13


def test_bfs_open_grid_equals_manhattan() -> None:
    city = City(10, 10)
    path = city.shortest_path((0, 0), (9, 9))
    assert path is not None
    assert path[0] == (0, 0) and path[-1] == (9, 9)
    assert len(path) - 1 == manhattan((0, 0), (9, 9))


def test_bfs_goes_around_wall() -> None:
    # Vertical wall at x=2 from y=0..3, gap at y=4.
    wall = [(2, y) for y in range(4)]
    city = City(5, 5, wall)
    path = city.shortest_path((0, 0), (4, 0))
    assert path is not None
    assert all(p not in city.blocked for p in path)
    # Must go down to y=4 and back: 4 down + 4 right + 4 up = 12 moves.
    assert len(path) - 1 == 12
    # Every step moves exactly one cell.
    for a, b in zip(path, path[1:]):
        assert manhattan(a, b) == 1


def test_unreachable_and_blocked_endpoints() -> None:
    wall = [(2, y) for y in range(5)]
    city = City(5, 5, wall)
    assert city.shortest_path((0, 0), (4, 4)) is None
    assert city.shortest_path((2, 0), (0, 0)) is None
    assert city.path_from((0, 0), (4, 4)) is None
    assert city.route_distance((0, 0), (4, 4)) is None


def test_bfs_tree_matches_shortest_path_and_is_cached() -> None:
    city = City.generate(20, 0.15, seed=3)
    rng = random.Random(1)
    src = city.random_free_cell(rng)
    for _ in range(20):
        dst = city.random_free_cell(rng)
        p1 = city.shortest_path(src, dst)
        p2 = city.path_from(src, dst)
        assert p1 is not None and p2 is not None
        assert len(p1) == len(p2) == city.route_distance(src, dst) + 1
    assert city.bfs_tree(src) is city.bfs_tree(src)


def test_generated_city_is_connected_and_reproducible() -> None:
    a = City.generate(30, 0.15, seed=11)
    b = City.generate(30, 0.15, seed=11)
    assert a.blocked == b.blocked
    free = a.free_cells()
    dist, _ = a.bfs_tree(free[0])
    assert len(dist) == len(free)          # every free cell reachable
    assert 0.10 < len(a.blocked) / (30 * 30) < 0.40


def test_neighbors_respect_bounds() -> None:
    city = City(3, 3, [(1, 0)])
    assert sorted(city.neighbors((0, 0))) == [(0, 1)]
    assert len(city.neighbors((1, 1))) == 3


def test_models_properties() -> None:
    r = Restaurant(0, "Biryani House", 3, 4)
    assert r.pos == (3, 4)
    rider = Rider(1, 0, 0)
    assert rider.is_free and rider.pos == (0, 0)
    o = Order(7, 0, 5, 5, created_at=10, vip=True)
    assert o.status == "waiting" and o.wait_time is None
    o.assigned_at, o.delivered_at = 15, 40
    assert o.wait_time == 5 and o.delivery_time == 30 and o.status == "delivered"
    assert o.customer_pos == (5, 5)
