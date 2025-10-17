
# 🛒 NaviStore – Smarter In-Store Navigation
![Shopping path simulation](https://i.imgur.com/HFGYCxl.png)

Shopping in a large retail store can quickly become a frustrating experience. Customers often waste time searching for familiar products, wandering through aisles without clear direction, and leaving with a sense of confusion. As a result, many shoppers prefer smaller or already familiar stores — limiting the potential of large retail environments.

NaviStore removes that friction.
The app provides real-time product locations, generates an optimized route to complete your shopping list efficiently, and alerts you to product availability.

👉 For customers: a faster, smoother, and more enjoyable shopping experience.
👉 For retailers: a powerful tool to improve customer satisfaction, streamline store navigation, and boost engagement with larger retail spaces.

# Api
## System Overview

NaviStore’s backend is built for scalability and performance, leveraging modern technologies:

- **Docker** for containerized deployment and easy environment management.
- **Elasticsearch** for advanced, distributed product catalog indexing, with a strong emphasis on full-text search capabilities for fast, relevant product queries.
- **Path Optimization Algorithms** (A*, Dijkstra, Best-First, TSP via Google OR-Tools) for efficient multi-point navigation and route planning.

This architecture ensures rapid development, robust search capabilities, and optimized in-store navigation, supporting both proof-of-concept and future production deployments.

## Elastic Search
Elastic Search is a powerful distributed search engine that perfectly suits our project's needs for several reasons:

1. **Full-Text Search Optimization**: We leverage Elastic Search for efficient full-text search across product titles, providing fast and relevant results.

2. **Document-Based Storage**: Products are indexed using their IDs as document identifiers (_id), enabling optimized multi-get (mget) operations for quick retrievals.

3. **Advanced Filtering**: The engine supports complex search parameters as filters without significant performance impact, allowing refined search results.

Perfect — here’s the **developer summary version** (about 1–2 pages).
It’s optimized for inclusion in an API documentation site or README — concise, scannable, and focused on what an engineer needs to know to use or extend the pathfinding system.

---

## Path Optimization

### Overview

The **Path Optimization Pipeline** computes the most efficient multi-point navigation routes in complex environments.
It combines **graph-based pathfinding** (A*, Dijkstra, Best-First) with **Traveling Salesman Problem (TSP)** optimization (Google OR-Tools) to generate minimal-distance routes through all Points of Interest (POIs). Enables to compute the best shopping path within the store layout.

![Shopping path simulation](https://i.imgur.com/FTxmcAq.png)
*Navistore path finding*

**Highlights**

* Supports A*, Dijkstra, and Best-First algorithms
* TSP solving via Google OR-Tools with greedy fallback
* Real-world coordinate mapping → grid representation
* Distance threshold filtering and A* fallback for missing paths
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


4. **Scalability**: Built for distributed systems, it can handle growing product catalogs efficiently.
## Layout Generator

We implemented a fast, hash-based versioning system to efficiently manage store layouts and SVG visualizations. By using **xxHash** (a high-speed, non-cryptographic hash function), we can quickly detect layout changes and avoid unnecessary SVG regeneration. This approach ensures that clients are always synchronized with the latest layout version, while minimizing redundant processing and network usage.

## Security
As this application is currently a proof of concept (POC), it is not intended for production deployment at this stage. We have implemented a basic API key system to control access and verify user rights. However, the API currently operates over HTTP, which means API keys are transmitted in plaintext and are not secure.

We recognize the importance of securing API communications with HTTPS and SSL certificates, especially to protect sensitive data and credentials. For this POC, we chose not to implement SSL due to the overhead of certificate management, renewal processes, and the potential variability in SSL policies across different deployment environments or client organizations. When moving towards production or public deployment, enabling HTTPS and robust security measures will be a top priority.

> ⚠️ Implement HTTPS for deployment. Transmitting API keys and sensitive data over HTTP is insecure and exposes users to potential risks. For production deployments, always use SSL certificates and enforce secure connections.

## Implementation Notes
- To delete index in developer mode: `Invoke-RestMethod -Method Delete -Uri "http://localhost:9200/products"`
- Run to reaload Hive's models in flutter : `flutter packages pub run build_runner build --delete-conflicting-outputs`


## Setup during developpement
- Launch docker desktop
- run from root: `docker compose up`
- run in flutter_app_navistore: `flutter run`

# Flutter Application

We developed the application using Flutter to ensure a responsive, cross-platform experience with low latency and consistent performance across devices.

## Product Search

The product search module includes category-based filters, allowing users to quickly locate items of interest.

<img src="https://i.imgur.com/EWbnjde.png" alt="Shopping path simulation" width="32%" style="display:inline-block; margin-right: 8px;"/>
<img src="https://i.imgur.com/XBBFfvL.png" alt="Shopping path simulation" width="32%" style="display:inline-block; margin-right: 8px;"/>
<img src="https://i.imgur.com/IGRODWo.png" alt="Shopping path simulation" width="32%" style="display:inline-block;"/>

## Shopping List

Users can create, rename, delete, and manage shopping lists, as well as assign products to specific lists.
The display of the shopping list can be toggled on or off.
Lists are synchronized with the database at setup, and any unavailable products are clearly flagged.
<div align="center">
<img src="https://i.imgur.com/JwSXv3b.png" alt="Shopping path simulation" width="48%" style="display:inline-block; margin-right: 8px;"/>
<img src="https://i.imgur.com/3qequ2M.png" alt="Shopping path simulation" width="48%" style="display:inline-block;"/>

<br/>
<img src="https://i.imgur.com/q0zHKWS.png" alt="Shopping path simulation" width="48" style="display:inline-block; margin-right: 8px;"/>
<img src="https://i.imgur.com/JzJk8qJ.png" alt="Shopping path simulation" width="48%" style="display:inline-block;"/>

</div>


## Map

The map is fully responsive and provides detailed contextual information, including:

- The total number of available products and total products in the selected lists
- The estimated total cost
- Astimated shopping duration, calculated from walking distance and average product pickup time.

Product information bubbles dynamically adjust their orientation to avoid overlapping or crossing map borders.  
<div align="center">

<img src="https://i.imgur.com/o8NQn1r.png" alt="Shopping path simulation" width="32%" style="display:inline-block; margin-right: 8px;"/>
<img src="https://i.imgur.com/VUoJ0XK.png" alt="Shopping path simulation" width="32%" style="display:inline-block; margin-right: 8px;"/>
<img src="https://i.imgur.com/DJCbljw.png" alt="Shopping path simulation" width="32%" style="display:inline-block;"/>

</div>
Directional arrows along the navigation path resize automatically based on the zoom level  
Users can pan, zoom, and navigate the map freely, and the information panel can be hidden for an uncluttered view.
<div align="center">

<img src="https://i.imgur.com/3lYJ2vv.png" alt="Shopping path simulation" width="48%" style="display:inline-block; margin-right: 8px;"/>
<img src="https://i.imgur.com/bXwcFiY.png" alt="Shopping path simulation" width="48%" style="display:inline-block; margin-right: 8px;"/>

</div>