"""Performance numbers computed from a finished simulation."""

from __future__ import annotations

from typing import Dict, List, Sequence

from .models import Order, Rider


def _mean(values: Sequence[float]) -> float:
    """Average, or 0.0 for an empty list. Time: O(n). Space: O(1)."""
    return sum(values) / len(values) if values else 0.0


def _percentile(values: Sequence[float], pct: float) -> float:
    """Nearest-rank percentile (pct in 0..100). Time: O(n log n). Space: O(n)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, int(round(pct / 100 * len(ordered))) - 1))
    return float(ordered[rank])


def compute_metrics(orders: List[Order], riders: List[Rider]) -> Dict[str, float]:
    """Summary metrics for one run.

    * avg_delivery_time - minutes from order placed to food delivered
    * avg_wait_time     - minutes an order waited for a rider to be assigned
    * utilization       - fraction of rider-time spent delivering, over the
                          span from the first order to the last delivery
    * orders_per_hour   - delivered orders / span in hours

    Time: O(N log N + R) (the sort is for the p90 percentile). Space: O(N).
    """
    delivered = [o for o in orders if o.delivered_at is not None]
    delivery_times = [o.delivery_time for o in delivered]
    waits = [o.wait_time for o in orders if o.wait_time is not None]
    vip_waits = [o.wait_time for o in orders if o.vip and o.wait_time is not None]
    normal_waits = [o.wait_time for o in orders if not o.vip and o.wait_time is not None]

    if delivered:
        start = min(o.created_at for o in orders)
        end = max(o.delivered_at for o in delivered)
        span = max(1, end - start)
    else:
        span = 1
    total_busy = sum(r.busy_time for r in riders)
    utilization = total_busy / (len(riders) * span) if riders else 0.0

    return {
        "total_orders": len(orders),
        "delivered": len(delivered),
        "avg_delivery_time": round(_mean(delivery_times), 2),
        "p90_delivery_time": round(_percentile(delivery_times, 90), 2),
        "avg_wait_time": round(_mean(waits), 2),
        "max_wait_time": max(waits) if waits else 0,
        "avg_vip_wait": round(_mean(vip_waits), 2),
        "avg_normal_wait": round(_mean(normal_waits), 2),
        "utilization": round(utilization, 4),
        "orders_per_hour": round(len(delivered) / (span / 60), 2),
        "span_minutes": span,
    }
