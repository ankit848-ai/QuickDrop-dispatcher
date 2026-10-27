# QuickDrop – Viva Notes (30 likely questions)

### Project basics

**1. What does QuickDrop do?**
It simulates a food delivery company for one day. Orders arrive over time; each one is assigned to the nearest free rider, the rider follows a shortest path (restaurant first, then customer), and when the rider finishes they take the most urgent waiting order. It measures how well the dispatching works.

**2. Why did you build the data structures yourself?**
The project is about data structures, so I wanted to show I understand how they work inside. `heapq`, `queue` and `networkx` are not used anywhere in `quickdrop/`.

**3. What are the main modules?**
`heap.py` (MinHeap, PriorityQueue), `linked_queue.py` (Queue), `models.py` (Order, Rider, Restaurant), `city.py` (grid, Manhattan, BFS), `dispatcher.py` (assign / complete), `strategies.py` (greedy vs naive), `simulator.py` (event loop), `metrics.py` (results).

**4. How is time modelled?**
In whole minutes. A rider moves one grid cell per minute, so a path of L cells takes L minutes. That keeps the maths simple: route length = travel time.

### Heap and priority queue

**5. What is a binary min-heap?**
A complete binary tree stored in an array where every parent is ≤ its children. The minimum is always at index 0. For index `i`: parent `(i-1)//2`, children `2i+1` and `2i+2`.

**6. Explain push and pop.**
Push: append at the end, then *sift up* – swap with the parent while smaller. Pop: take the root, move the last item to the root, then *sift down* – swap with the smaller child while larger. Both walk one root-to-leaf path, so O(log n).

**7. Why is building a heap from a list O(n) and not O(n log n)?**
Floyd's bottom-up heapify sifts down from the last parent to the root. Half the nodes are leaves (no work), a quarter move at most 1 level, an eighth at most 2… The sum n/4·1 + n/8·2 + … is bounded by n, so it's O(n).

**8. How do you break ties in the heap?**
Each entry is stored as `(key, counter, item)`. The counter increases on every push, so equal keys come out in insertion order (FIFO), and Python never has to compare two `Order` objects directly.

**9. What is the priority of a waiting order?**
The key `(0 if VIP else 1, created_at, id)`. Tuples compare left to right, so every VIP comes before every normal order, and within the same type the older order comes first.

**10. Where do you use heaps in the project?**
Three places: (a) choosing the nearest free rider, (b) the waiting-orders priority queue, (c) the simulator's event list ordered by timestamp.

### Queue and BFS

**11. Why a linked-list queue instead of a Python list?**
`list.pop(0)` shifts every element, O(n). With head and tail pointers, enqueue at the tail and dequeue at the head are both O(1).

**12. Explain BFS.**
Start from the source, put it in a queue, mark it visited. Repeatedly dequeue a cell and enqueue all unvisited free neighbours, remembering each one's parent. BFS visits cells in increasing distance, so the first time we reach the goal is via a shortest path. Follow parents back to rebuild the path.

**13. Why BFS and not Dijkstra?**
Every move costs exactly 1 minute – the graph is unweighted. BFS gives shortest paths in O(V + E) without a priority queue. Dijkstra would be needed if roads had different speeds.

**14. What is the complexity of BFS here?**
V = W × H cells, each has ≤ 4 edges, so O(V + E) = O(W × H) time and space.

**15. What optimisation did you make for BFS?**
Instead of one BFS per trip, I run one full BFS from each restaurant and cache the distance and parent maps in a dictionary. Since the grid is undirected, the same tree gives both legs: restaurant → rider (reversed) and restaurant → customer. After the first BFS from a restaurant, each route costs only O(path length).

**16. What if a customer is unreachable?**
When the city is generated, I run BFS from the centre and mark every free cell it could not reach as blocked. So the whole city is one connected region and every trip is possible.

### Dispatching and strategies

**17. How is the nearest rider chosen?**
Free riders are put into a MinHeap keyed by Manhattan distance to the restaurant (heapify O(F)), and the top is popped (O(log F)). Total O(F) per order.

**18. Why Manhattan distance for choosing but BFS for routing?**
Manhattan is O(1) per rider, so comparing all free riders is cheap. BFS is exact but O(W × H). Manhattan is a good lower-bound estimate on a grid; the actual trip uses BFS.

**19. What is the naive strategy?**
Scan the rider list in id order and take the first free rider, ignoring distance. O(R) per order. It is a baseline to show the value of choosing by distance.

**20. If the heap is rebuilt every time, is it really faster than a linear scan?**
Not asymptotically – both are O(F)/O(R) per decision. The heap wins on *quality*, because it picks the nearest rider, which cuts travel time. A heap would also make it easy to get the k nearest riders in O(F + k log F). I state this honestly in the report.

**21. What happens when no rider is free?**
The order is enqueued in the waiting priority queue (O(log W)). When any rider finishes a delivery, they are freed at the customer's location and immediately dequeue the top waiting order.

**22. Which hash maps do you use?**
`riders` (id → Rider), `free` (id → Rider, O(1) add/remove), `restaurants` (id → Restaurant), `orders_by_id`, the `blocked` set of cells, and the BFS cache (source cell → trees).

### Simulation and metrics

**23. What does "event-driven" mean?**
Instead of ticking every minute, I keep future events in a min-heap ordered by time and jump straight to the next one. Two event types: ORDER (an order is placed) and DONE (a rider finishes). Idle minutes cost nothing.

**24. What if two events happen at the same minute?**
The heap key is `(time, kind)` with DONE = 0 and ORDER = 1, so deliveries finish first. That frees riders before new orders at the same minute are dispatched.

**25. What is the overall complexity of a simulation?**
O(N log N) for the event heap, plus O(N × F) for greedy dispatch decisions, plus O(N × L) for routes, plus O(restaurants × W × H) for the cached BFS trees.

**26. How do you define each metric?**
Delivery time = delivered − created. Wait time = assigned − created. Utilization = total minutes riders spent delivering ÷ (riders × span from first order to last delivery). Orders/hour = delivered ÷ span in hours.

**27. How is the data generated?**
`data/generate_data.py` uses a seeded `random.Random`, so the same seed gives the same city and orders. Order times are 40% around lunch (12:30), 45% around dinner (20:30) and 15% spread across the day; about 10% are VIP.

**28. What did the benchmarks show?**
The greedy heap strategy gives much lower delivery and wait times than the naive one, especially when riders are scarce and queues build up (see the Results section in REPORT.md for the exact numbers).

### Deployment and testing

**29. How is it deployed?**
`api/index.py` is a FastAPI app that Vercel runs as a Python serverless function; `vercel.json` rewrites `/api/*` to it and serves `public/` as a static site. Inputs are capped (≤ 200 riders, ≤ 2000 orders) so a request finishes in under the 10-second limit.

**30. How did you test it?**
pytest unit tests for every module: heap order against `sorted()`, random interleaved push/pop, BFS around walls, unreachable cells, VIP-first queue order, a hand-calculated single-rider timeline, route continuity (each step moves one cell and avoids obstacles), and API tests with FastAPI's TestClient including the input caps and a timing check.
