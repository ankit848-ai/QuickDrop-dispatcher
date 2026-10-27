"""Benchmark greedy-heap vs naive-linear assignment.

Runs every combination of riders in {10, 50, 200} and orders in
{100, 1000, 10000} on the same 50x50 city and seed, for both strategies,
then writes ``results/benchmark.csv`` and PNG charts.

Usage (from the project root):
    python benchmarks/benchmark.py
"""

from __future__ import annotations

import csv
import os
import sys
import time
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from data.generate_data import generate_scenario  # noqa: E402
from quickdrop.simulator import simulate  # noqa: E402

RIDERS = [10, 50, 200]
ORDERS = [100, 1000, 10000]
STRATEGIES = ["greedy", "naive"]
CITY_SIZE = 50
SEED = 42
RESULTS = os.path.join(ROOT, "benchmarks", "results")


def run_all() -> List[Dict[str, float]]:
    """Run every (riders, orders, strategy) case. Time: dominated by the 10k-order runs."""
    rows: List[Dict[str, float]] = []
    for riders in RIDERS:
        for orders in ORDERS:
            for strategy in STRATEGIES:
                s = generate_scenario(riders, orders, CITY_SIZE, SEED)
                start = time.perf_counter()
                result = simulate(s.city, s.restaurants, s.riders, s.orders, strategy)
                wall = (time.perf_counter() - start) * 1000
                m = result.metrics
                row = {
                    "riders": riders, "orders": orders, "strategy": strategy,
                    "avg_delivery_time": m["avg_delivery_time"],
                    "p90_delivery_time": m["p90_delivery_time"],
                    "avg_wait_time": m["avg_wait_time"],
                    "utilization": m["utilization"],
                    "orders_per_hour": m["orders_per_hour"],
                    "runtime_ms": round(wall, 1),
                }
                rows.append(row)
                print(f"{riders:>4} riders {orders:>6} orders {strategy:>6}: "
                      f"deliv {row['avg_delivery_time']:>8.1f}  wait {row['avg_wait_time']:>8.1f}  "
                      f"util {row['utilization']:.3f}  {row['runtime_ms']:>8.1f} ms")
    return rows


def save_csv(rows: List[Dict[str, float]]) -> str:
    """Write rows to results/benchmark.csv. Time: O(rows)."""
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "benchmark.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def save_charts(rows: List[Dict[str, float]]) -> List[str]:
    """One grouped bar chart per metric: x = (riders, orders), bars = strategy."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"greedy": "#2a9d8f", "naive": "#e76f51"}
    labels = [f"{r}R/{o}O" for r in RIDERS for o in ORDERS]
    metrics = [
        ("avg_delivery_time", "Average delivery time (min)"),
        ("avg_wait_time", "Average wait for a rider (min)"),
        ("utilization", "Rider utilization (fraction busy)"),
        ("runtime_ms", "Simulation runtime (ms, log scale)"),
    ]
    paths = []
    for key, title in metrics:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        width = 0.38
        for i, strategy in enumerate(STRATEGIES):
            values = [next(r[key] for r in rows if r["riders"] == rd and r["orders"] == od
                           and r["strategy"] == strategy) for rd in RIDERS for od in ORDERS]
            xs = [x + (i - 0.5) * width for x in range(len(labels))]
            ax.bar(xs, values, width, label=strategy, color=colors[strategy])
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30)
        ax.set_title(title)
        ax.set_xlabel("riders (R) / orders (O)")
        if key == "runtime_ms":
            ax.set_yscale("log")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        path = os.path.join(RESULTS, f"{key}.png")
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(path)
    return paths


if __name__ == "__main__":
    data = run_all()
    print("wrote", save_csv(data))
    for p in save_charts(data):
        print("wrote", p)
