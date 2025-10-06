## Elastic Search
Elastic Search is a powerful distributed search engine that perfectly suits our project's needs for several reasons:

1. **Full-Text Search Optimization**: We leverage Elastic Search for efficient full-text search across product titles, providing fast and relevant results.

2. **Document-Based Storage**: Products are indexed using their IDs as document identifiers (_id), enabling optimized multi-get (mget) operations for quick retrievals.

3. **Advanced Filtering**: The engine supports complex search parameters as filters without significant performance impact, allowing refined search results.

Perfect — here’s the **developer summary version** (about 1–2 pages).
It’s optimized for inclusion in an API documentation site or README — concise, scannable, and focused on what an engineer needs to know to use or extend the pathfinding system.

---

## Path Optimization Pipeline

### Overview

The **Path Optimization Pipeline** computes the most efficient multi-point navigation routes in complex environments.
It combines **graph-based pathfinding** (A*, Dijkstra, Best-First) with **Traveling Salesman Problem (TSP)** optimization (Google OR-Tools) to generate minimal-distance routes through all Points of Interest (POIs). Enables to compute the best shopping path within the store layout.

![Shopping path simulation](https://i.imgur.com/xEi6ycx.png)
*Demo of the Path Optimization Pipeline*

**Highlights**

* Supports A*, Dijkstra, and Best-First algorithms
* TSP solving via Google OR-Tools with greedy fallback
* Real-world coordinate mapping → grid representation
* A* fallback for missing paths
* Built-in caching and performance optimizations
* Full REST API integration



---

### Workflow Summary

1. **Layout Management**
   Loads and validates the store layout, applies versioning and SVG visualization.

2. **POI Mapping**
   Converts POI coordinates from real-world units (cm) to grid indices and validates them.

3. **Pathfinding**
   Computes all-pairs shortest paths between POIs using the selected algorithm (A*, Dijkstra, Best-First).
   Produces a **distance matrix** for the TSP solver.

4. **TSP Optimization**
   Determines the optimal POI visiting order with Google OR-Tools (configurable runtime and accuracy).
   Falls back to greedy heuristics if OR-Tools is unavailable.

5. **Path Reconstruction**
   Reassembles the final route based on TSP results, with **A*** fallback for missing segments.

6. **Response Serialization**
   Converts data to JSON-safe types and adds performance metrics, fallback statistics, and error details.

---

### Algorithm Overview

| Algorithm      | Optimal | Performance | Typical Use             |
| -------------- | ------- | ----------- | ----------------------- |
| **A***         | ✅       | ⚡⚡          | Default – good balance  |
| **Dijkstra**   | ✅       | ⚡           | Full optimality, slower |
| **Best-First** | ❌       | ⚡⚡⚡         | Fast for large grids    |

**TSP Solver:**

* **Primary:** Google OR-Tools (with runtime & optimality limits)
* **Fallback:** Nearest Neighbor + 2-opt refinement

**Optimizations:**

* Distance threshold filtering (very effective for large grids)
* Sparse matrix path storage
* NumPy vectorization for fast operations
* A* fallback ensures full route generation

---

### API Endpoints

**`POST /upload_layout`**
Uploads and validates a layout (HDF5 grid). Returns layout hash.

**`POST /optimize_path`**
Main endpoint — runs pathfinding + TSP.
**Input:** POI list, algorithm, distance threshold, diagonal flag, max runtime
**Output:** Full path, total distance, visiting order, metrics.

**`GET /pathfinding_algorithms`**
Lists available algorithms and performance notes.

---

### Example Usage

```python
response = requests.post("/optimize_path", json={
    "poi_coordinates": [{"x":150,"y":200},{"x":450,"y":300}],
    "pathfinding_algorithm": "astar",
    "distance_threshold": 2000,
    "max_runtime": 30
})
print(response.json()["total_distance"])
```

**Recommendations**

* Small grids → `A*`
* Large grids → `Best-First`
* Critical precision → `Dijkstra`

---

### Future Directions

* Hierarchical or Jump Point Search for large maps, C or C++ implementation
* Parallel and GPU acceleration
* Persistent caching and cloud scaling

---

### Summary

The Path Optimization Pipeline offers a **modular, efficient, and production-ready** framework for route computation.
Its flexible algorithm selection, caching, and robust fallback logic make it ideal for real-time navigation and optimization applications.


4. **Scalability**: Built for distributed systems, it can handle growing product catalogs efficiently.

## Implementation Notes
- To delete index in developer mode: `Invoke-RestMethod -Method Delete -Uri "http://localhost:9200/products"`

## Setup during developpement
- Launch docker desktop
- run from root: `docker compose up`
- run in flutter_app_navistore: `flutter run`