"""Generate a reproducible city, restaurants, riders and orders.

Orders follow a realistic daily pattern: a lunch peak around 12:30, a bigger
dinner peak around 20:30, and some background orders during the day.
About 10% of orders are VIP. The same ``seed`` always gives the same data.

Usage (from the project root):
    python -m data.generate_data --riders 50 --orders 1000 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from dataclasses import dataclass
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quickdrop.city import City  # noqa: E402
from quickdrop.models import Order, Restaurant, Rider  # noqa: E402

DAY_START = 8 * 60          # 08:00
DAY_END = 24 * 60 - 1       # 23:59
LUNCH_PEAK, LUNCH_SD = 12 * 60 + 30, 45
DINNER_PEAK, DINNER_SD = 20 * 60 + 30, 60

FOOD_WORDS = ["Biryani", "Dosa", "Pizza", "Momo", "Tandoor", "Burger", "Thali",
              "Chaat", "Noodle", "Kebab", "Paratha", "Idli", "Rolls", "Curry"]
PLACE_WORDS = ["House", "Corner", "Express", "Point", "Kitchen", "Hub", "Junction"]


@dataclass
class Scenario:
    """Everything needed for one simulation run. Space: O(W*H + N + R)."""

    city: City
    restaurants: List[Restaurant]
    riders: List[Rider]
    orders: List[Order]


def generate_restaurants(city: City, count: int, rng: random.Random) -> List[Restaurant]:
    """Restaurants on distinct free cells. Time: O(count) expected. Space: O(count)."""
    used = set()
    result: List[Restaurant] = []
    while len(result) < count:
        p = city.random_free_cell(rng)
        if p in used:
            continue
        used.add(p)
        name = f"{rng.choice(FOOD_WORDS)} {rng.choice(PLACE_WORDS)}"
        result.append(Restaurant(len(result), name, p[0], p[1]))
    return result


def generate_riders(city: City, count: int, rng: random.Random) -> List[Rider]:
    """Riders at random free cells. Time: O(count). Space: O(count)."""
    riders: List[Rider] = []
    for i in range(count):
        x, y = city.random_free_cell(rng)
        riders.append(Rider(i, x, y))
    return riders


def _order_minute(rng: random.Random) -> int:
    """One order time: 40% lunch, 45% dinner, 15% uniform. Time: O(1)."""
    roll = rng.random()
    if roll < 0.40:
        t = rng.gauss(LUNCH_PEAK, LUNCH_SD)
    elif roll < 0.85:
        t = rng.gauss(DINNER_PEAK, DINNER_SD)
    else:
        t = rng.uniform(DAY_START, DAY_END)
    return int(min(DAY_END, max(DAY_START, t)))


def generate_orders(city: City, restaurants: List[Restaurant], count: int,
                    rng: random.Random, vip_ratio: float = 0.10) -> List[Order]:
    """Orders sorted by time; ids follow time order.

    Time: O(count log count) for the sort. Space: O(count).
    """
    times = sorted(_order_minute(rng) for _ in range(count))
    orders: List[Order] = []
    for i, t in enumerate(times):
        restaurant = rng.choice(restaurants)
        cx, cy = city.random_free_cell(rng)
        orders.append(Order(i, restaurant.id, cx, cy, created_at=t,
                            vip=rng.random() < vip_ratio))
    return orders


def generate_scenario(riders: int = 50, orders: int = 1000, city_size: int = 50,
                      seed: int = 42, restaurants: int = 0,
                      obstacle_ratio: float = 0.12) -> Scenario:
    """Build a full scenario. ``restaurants=0`` means "pick a size-based default".

    Time: O(size^2 + N log N + R). Space: O(size^2 + N + R).
    """
    rng = random.Random(seed)
    city = City.generate(city_size, obstacle_ratio, seed)
    n_rest = restaurants or max(3, min(40, city_size * city_size // 150))
    rest = generate_restaurants(city, n_rest, rng)
    return Scenario(city, rest, generate_riders(city, riders, rng),
                    generate_orders(city, rest, orders, rng))


def save_csv(scenario: Scenario, folder: str) -> List[str]:
    """Write restaurants.csv, riders.csv, orders.csv, obstacles.csv.

    Time: O(N + R + B). Space: O(1) extra.
    """
    os.makedirs(folder, exist_ok=True)
    tables = {
        "restaurants.csv": (["id", "name", "x", "y"],
                            [[r.id, r.name, r.x, r.y] for r in scenario.restaurants]),
        "riders.csv": (["id", "x", "y"], [[r.id, r.x, r.y] for r in scenario.riders]),
        "orders.csv": (["id", "restaurant_id", "customer_x", "customer_y", "created_at", "vip"],
                       [[o.id, o.restaurant_id, o.customer_x, o.customer_y, o.created_at, int(o.vip)]
                        for o in scenario.orders]),
        "obstacles.csv": (["x", "y"], sorted([list(p) for p in scenario.city.blocked])),
    }
    paths = []
    for name, (header, rows) in tables.items():
        path = os.path.join(folder, name)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        paths.append(path)
    return paths


def main(argv: List[str] | None = None) -> None:
    """Command-line entry point. Time: O(size^2 + N log N). Space: O(size^2 + N)."""
    parser = argparse.ArgumentParser(description="Generate QuickDrop data as CSV")
    parser.add_argument("--riders", type=int, default=50)
    parser.add_argument("--orders", type=int, default=1000)
    parser.add_argument("--city-size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    args = parser.parse_args(argv)
    scenario = generate_scenario(args.riders, args.orders, args.city_size, args.seed)
    for path in save_csv(scenario, args.out):
        print("wrote", path)


if __name__ == "__main__":
    main()
