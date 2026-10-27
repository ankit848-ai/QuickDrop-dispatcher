"""QuickDrop HTTP API (FastAPI). Runs as a Vercel Python serverless function.

    GET  /api/health    -> {"status": "ok"}
    POST /api/simulate  -> full run with animation frames
    POST /api/compare   -> greedy vs naive metrics on identical inputs

Locally, ``uvicorn api.index:app --reload`` also serves the ``public/`` UI.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Literal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from data.generate_data import Scenario, generate_scenario  # noqa: E402
from quickdrop.simulator import simulate  # noqa: E402

MAX_FRAMES = 300

app = FastAPI(title="QuickDrop API", version="1.0.0")


class SimRequest(BaseModel):
    """Simulation inputs, capped so a run finishes well under 10 s."""

    riders: int = Field(30, ge=1, le=200)
    orders: int = Field(500, ge=1, le=2000)
    city_size: int = Field(50, ge=10, le=80)
    strategy: Literal["greedy", "naive"] = "greedy"
    seed: int = Field(42, ge=0, le=10**9)


def _scenario(req: SimRequest) -> Scenario:
    """Fresh, deterministic scenario for the request. Time: O(size^2 + N log N)."""
    return generate_scenario(req.riders, req.orders, req.city_size, req.seed)


@app.get("/api/health")
def health() -> Dict[str, str]:
    """Liveness check. Time: O(1)."""
    return {"status": "ok"}


@app.post("/api/simulate")
def run_simulation(req: SimRequest) -> Dict[str, Any]:
    """Run one strategy and return map, entities, frames and metrics.

    Order routes are sent as flat cell indices (y * size + x) to keep the
    JSON small. Time: O(simulation + frames * R). Space: O(N * L + frames * R).
    """
    s = _scenario(req)
    first = min(o.created_at for o in s.orders)
    last = max(o.created_at for o in s.orders)
    frame_every = max(1, -(-(last - first + 120) // MAX_FRAMES))   # ceiling division
    result = simulate(s.city, s.restaurants, s.riders, s.orders, req.strategy, frame_every)
    size = req.city_size
    return {
        "request": req.model_dump(),
        "city": {"size": size, "obstacles": sorted([list(p) for p in s.city.blocked])},
        "restaurants": [{"id": r.id, "name": r.name, "x": r.x, "y": r.y} for r in s.restaurants],
        "orders": [{
            "id": o.id, "restaurant_id": o.restaurant_id, "x": o.customer_x, "y": o.customer_y,
            "created_at": o.created_at, "vip": o.vip, "rider_id": o.rider_id,
            "assigned_at": o.assigned_at, "picked_up_at": o.picked_up_at,
            "delivered_at": o.delivered_at,
            "path": [y * size + x for x, y in o.path],
        } for o in result.orders],
        "frame_every": frame_every,
        "frames": result.frames,
        "metrics": result.metrics,
        "runtime_ms": result.runtime_ms,
        "events_processed": result.events_processed,
    }


@app.post("/api/compare")
def compare(req: SimRequest) -> Dict[str, Any]:
    """Run greedy and naive on identical generated inputs. Time: 2 x simulation."""
    out: Dict[str, Any] = {"request": req.model_dump()}
    for strategy in ("greedy", "naive"):
        s = _scenario(req)
        result = simulate(s.city, s.restaurants, s.riders, s.orders, strategy)
        out[strategy] = {**result.metrics, "runtime_ms": result.runtime_ms}
    return out


# Serve the UI when running locally (on Vercel, public/ is served by the CDN).
_PUBLIC = os.path.join(ROOT, "public")
if os.path.isdir(_PUBLIC) and not os.environ.get("VERCEL"):
    app.mount("/", StaticFiles(directory=_PUBLIC, html=True), name="public")
