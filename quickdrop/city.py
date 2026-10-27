"""The city: a 2D grid with blocked cells, Manhattan distance and BFS routing.

Coordinates are (x, y) with 0 <= x < width and 0 <= y < height. A rider can
move up/down/left/right into any cell that is not blocked. Every move costs
1 minute, so the grid is an *unweighted graph* and BFS gives shortest paths.
"""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .linked_queue import Queue
from .models import Point

# The four directions a rider can move in.
DIRECTIONS: Tuple[Point, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def manhattan(a: Point, b: Point) -> int:
    """|x1 - x2| + |y1 - y2| - grid distance ignoring obstacles.

    Used to *quickly estimate* which rider is nearest.
    Time: O(1). Space: O(1).
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class City:
    """Grid map with obstacles.

    ``blocked`` is a hash set, so "is this cell blocked?" is O(1).
    BFS results from a source cell are cached in a dict (hash map) because
    the same restaurants are routed from again and again.

    Space: O(W*H) in the worst case (blocked set + cached BFS trees).
    """

    def __init__(self, width: int, height: int, blocked: Iterable[Point] = ()) -> None:
        """Create a width x height grid. Time: O(B) for B blocked cells. Space: O(B)."""
        if width <= 0 or height <= 0:
            raise ValueError("city must be at least 1x1")
        self.width: int = width
        self.height: int = height
        self.blocked: Set[Point] = set(blocked)
        # source cell -> (distance map, parent map)
        self._tree_cache: Dict[Point, Tuple[Dict[Point, int], Dict[Point, Optional[Point]]]] = {}

    # ---------- basic cell queries ----------

    def in_bounds(self, p: Point) -> bool:
        """True if p lies inside the grid. Time: O(1). Space: O(1)."""
        return 0 <= p[0] < self.width and 0 <= p[1] < self.height

    def is_free(self, p: Point) -> bool:
        """True if p is inside the grid and not blocked. Time: O(1). Space: O(1)."""
        return self.in_bounds(p) and p not in self.blocked

    def neighbors(self, p: Point) -> List[Point]:
        """Free cells reachable from p in one move. Time: O(1). Space: O(1)."""
        x, y = p
        result: List[Point] = []
        for dx, dy in DIRECTIONS:
            q = (x + dx, y + dy)
            if self.is_free(q):
                result.append(q)
        return result

    def free_cells(self) -> List[Point]:
        """All non-blocked cells, row by row. Time: O(W*H). Space: O(W*H)."""
        return [(x, y) for y in range(self.height) for x in range(self.width)
                if (x, y) not in self.blocked]

    # ---------- BFS ----------

    def shortest_path(self, start: Point, goal: Point) -> Optional[List[Point]]:
        """BFS shortest path from start to goal (inclusive), or None if unreachable.

        BFS explores cells in rings of increasing distance using a FIFO queue,
        so the first time we reach ``goal`` it is by a shortest route.
        We stop as soon as the goal is dequeued (early exit).

        Time: O(V + E) = O(W*H) worst case. Space: O(W*H).
        """
        if not self.is_free(start) or not self.is_free(goal):
            return None
        parent: Dict[Point, Optional[Point]] = {start: None}
        queue: Queue[Point] = Queue()
        queue.enqueue(start)
        while not queue.is_empty():
            cell = queue.dequeue()
            if cell == goal:
                return self._walk_back(parent, goal)
            for nxt in self.neighbors(cell):
                if nxt not in parent:          # not visited yet
                    parent[nxt] = cell
                    queue.enqueue(nxt)
        return None

    def bfs_tree(self, source: Point) -> Tuple[Dict[Point, int], Dict[Point, Optional[Point]]]:
        """Full BFS from ``source``: distance and parent of every reachable cell.

        Cached per source, so repeated calls are O(1).
        Time: O(W*H) first call, O(1) after. Space: O(W*H) per cached source.
        """
        if source in self._tree_cache:
            return self._tree_cache[source]
        dist: Dict[Point, int] = {source: 0}
        parent: Dict[Point, Optional[Point]] = {source: None}
        queue: Queue[Point] = Queue()
        queue.enqueue(source)
        while not queue.is_empty():
            cell = queue.dequeue()
            for nxt in self.neighbors(cell):
                if nxt not in dist:
                    dist[nxt] = dist[cell] + 1
                    parent[nxt] = cell
                    queue.enqueue(nxt)
        self._tree_cache[source] = (dist, parent)
        return dist, parent

    def path_from(self, source: Point, target: Point) -> Optional[List[Point]]:
        """Shortest path source -> target using the cached BFS tree of source.

        Time: O(L) for path length L (plus O(W*H) once to build the tree).
        Space: O(L).
        """
        _, parent = self.bfs_tree(source)
        if target not in parent:
            return None
        return self._walk_back(parent, target)

    def route_distance(self, source: Point, target: Point) -> Optional[int]:
        """BFS (obstacle-aware) distance, or None if unreachable.

        Time: O(1) after the tree of source is cached. Space: O(1).
        """
        dist, _ = self.bfs_tree(source)
        return dist.get(target)

    @staticmethod
    def _walk_back(parent: Dict[Point, Optional[Point]], goal: Point) -> List[Point]:
        """Follow parent pointers from goal back to the source, then reverse.

        Time: O(L). Space: O(L).
        """
        path: List[Point] = []
        cell: Optional[Point] = goal
        while cell is not None:
            path.append(cell)
            cell = parent[cell]
        path.reverse()
        return path

    # ---------- random city generation ----------

    @classmethod
    def generate(cls, size: int = 50, obstacle_ratio: float = 0.12,
                 seed: Optional[int] = None) -> "City":
        """Make a size x size city with small rectangular "buildings" as obstacles.

        After placing obstacles we run one BFS from the centre and block every
        free cell it could not reach, so the whole city is connected and every
        delivery is possible.

        Time: O(size^2). Space: O(size^2).
        """
        rng = random.Random(seed)
        blocked: Set[Point] = set()
        target = int(size * size * obstacle_ratio)
        while len(blocked) < target:
            w, h = rng.randint(1, 3), rng.randint(1, 3)
            x0, y0 = rng.randrange(size), rng.randrange(size)
            for x in range(x0, min(x0 + w, size)):
                for y in range(y0, min(y0 + h, size)):
                    blocked.add((x, y))
        city = cls(size, size, blocked)

        # Pick the free cell closest to the centre as the BFS start.
        centre = (size // 2, size // 2)
        start = min(city.free_cells(), key=lambda p: manhattan(p, centre))
        reachable, _ = city.bfs_tree(start)
        for p in city.free_cells():
            if p not in reachable:
                city.blocked.add(p)
        city._tree_cache.clear()     # blocked set changed -> old trees invalid
        return city

    def random_free_cell(self, rng: random.Random) -> Point:
        """Pick a random non-blocked cell (rejection sampling).

        Time: O(1) expected (most cells are free). Space: O(1).
        """
        while True:
            p = (rng.randrange(self.width), rng.randrange(self.height))
            if p not in self.blocked:
                return p
