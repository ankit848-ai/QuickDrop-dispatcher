# QuickDrop – Build Progress

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Setup, `heap.py`, `linked_queue.py`, tests | ✅ Done |
| 2 | `models.py`, `city.py` (Manhattan + BFS), tests | ✅ Done |
| 3 | `dispatcher.py`, `strategies.py`, tests | ✅ Done |
| 4 | Data generator, `simulator.py`, `metrics.py`, tests | ✅ Done |
| 5 | Benchmarks (CSV + charts in `benchmarks/results/`) | ✅ Done |
| 6 | FastAPI backend + API tests, verified locally with uvicorn | ✅ Done |
| 7 | Web frontend, verified in a browser (desktop + mobile) | ✅ Done |
| 8 | Vercel config (`vercel.json`, `.vercelignore`, split requirements) | ✅ Done (see fallback) |
| 9 | README, REPORT (real numbers), VIVA_NOTES | ✅ Done |
| 10 | Final check | ✅ Done |

**Tests:** 44 passing (`python -m pytest -q`).

## Notes / fallbacks

- Python 3.12.10, venv in `.venv`. `pytest.ini` sets `pythonpath = .` so tests import `quickdrop` directly.
- MinHeap stores `(key, counter, item)` triples: the counter makes ties FIFO and means
  items themselves never need to be comparable.
- BFS optimisation: one full BFS tree per restaurant is cached; both trip legs
  (restaurant→rider reversed, restaurant→customer) come from it.
- City generation blocks any free cell unreachable from the centre, so every trip has a route.
- The data generator lives in `data/generate_data.py` (made a package with `data/__init__.py`)
  so the API can import it; the CLI is `python -m data.generate_data`.
- **Stage 8 fallback:** Vercel CLI 65.4.0 installed, but `vercel dev` needs a logged-in,
  linked project and the machine is logged out (`vercel login` is an interactive step for the
  owner). Instead, the function was verified the way Vercel runs it: imported from a different
  working directory with `VERCEL=1` (static mount disabled), and the max-size request
  (200 riders, 2000 orders, 80×80) returned 200 in 0.8 s, well under the 10 s limit.
  Its JSON is ~2.1 MB, under Vercel's 4.5 MB response cap (routes are sent as flat cell indices).
- Frontend default is 60 riders / 500 orders: 30 riders overloaded the city and made the
  demo all-red.
- Utilization is shown without a "winner" highlight in the comparison table: higher utilization
  for the naive strategy means riders travel further, not that they work better.
- Benchmark finding: under heavy overload both strategies converge, because freed riders always
  take the top waiting order (spec rule), which does not depend on the strategy.
