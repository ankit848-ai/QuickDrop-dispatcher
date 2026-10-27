# QuickDrop – Build Progress

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Setup, `heap.py`, `linked_queue.py`, tests | ✅ Done |
| 2 | `models.py`, `city.py` (Manhattan + BFS), tests | ⏳ |
| 3 | `dispatcher.py`, `strategies.py`, tests | ⏳ |
| 4 | Data generator, `simulator.py`, `metrics.py`, tests | ⏳ |
| 5 | Benchmarks (CSV + charts) | ⏳ |
| 6 | FastAPI backend + API tests | ⏳ |
| 7 | Web frontend | ⏳ |
| 8 | Vercel config + `vercel dev` | ⏳ |
| 9 | README, REPORT, VIVA_NOTES | ⏳ |
| 10 | Final check | ⏳ |

## Notes / fallbacks
- Python 3.12.10, venv in `.venv`. `pytest.ini` sets `pythonpath = .` so tests import `quickdrop` directly.
- MinHeap stores `(key, counter, item)` triples: the counter makes ties FIFO and means
  items themselves never need to be comparable.
