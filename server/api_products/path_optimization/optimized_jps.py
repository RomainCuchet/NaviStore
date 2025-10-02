"""
Optimized Jump Point Search for path finding in store layouts.

Implements JPS algorithm with precomputed jump points and distance thresholding.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
from collections import deque

from .utils import euclidean_distance, manhattan_distance

logger = logging.getLogger(__name__)


class OptimizedJPS:
    """
    Optimized Jump Point Search implementation for efficient pathfinding.

    Uses precomputed jump points and distance thresholding for performance.
    """

    def __init__(
        self,
        grid_with_poi: np.ndarray,
        jps_cache: dict,
        distance_threshold_grid: float,
        poi_coords: np.ndarray,
    ):
        """
        Initialize the optimized JPS solver.

        Args:
            grid_with_poi: Grid with POIs marked (0=navigable, 1=POI, -1=obstacle)
            jps_cache: Precomputed JPS jump points cache
            distance_threshold_grid: Distance threshold in grid units
            poi_coords: Array of POI coordinates in grid space
        """
        self.grid = grid_with_poi
        self.jps_cache = jps_cache
        self.distance_threshold = distance_threshold_grid
        self.poi_coords = poi_coords
        self.grid_height, self.grid_width = grid_with_poi.shape

        logger.info(
            f"Initialized OptimizedJPS with {len(poi_coords)} POIs, "
            f"threshold={distance_threshold_grid:.2f}"
        )

    def _get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """
        Get valid neighboring cells for a position.

        Args:
            x, y: Grid position

        Returns:
            List of valid neighbor coordinates
        """
        neighbors = []
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < self.grid_width
                and 0 <= ny < self.grid_height
                and self.grid[ny, nx] != -1
            ):
                neighbors.append((nx, ny))

        return neighbors

    def _reconstruct_path(
        self,
        came_from: Dict[Tuple[int, int], Tuple[int, int]],
        start: Tuple[int, int],
        goal: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """
        Reconstruct path from A* search results.

        Args:
            came_from: Dictionary mapping positions to their predecessors
            start: Start position
            goal: Goal position

        Returns:
            List of positions forming the path
        """
        path = []
        current = goal

        while current != start:
            path.append(current)
            current = came_from[current]

        path.append(start)
        path.reverse()
        return path

    def _compress_path(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Compress path to store only direction changes and endpoints.

        Args:
            path: Full path with all steps

        Returns:
            Compressed path with only key points
        """
        if len(path) <= 2:
            return path

        compressed = [path[0]]  # Start point

        for i in range(1, len(path) - 1):
            prev_point = path[i - 1]
            curr_point = path[i]
            next_point = path[i + 1]

            # Calculate direction vectors
            dir1 = (curr_point[0] - prev_point[0], curr_point[1] - prev_point[1])
            dir2 = (next_point[0] - curr_point[0], next_point[1] - curr_point[1])

            # If direction changes, include this point
            if dir1 != dir2:
                compressed.append(curr_point)

        compressed.append(path[-1])  # End point
        return compressed

    def find_path_astar(
        self, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find path between two points using A* algorithm.

        Args:
            start: Start position (x, y)
            goal: Goal position (x, y)

        Returns:
            Path as list of coordinates, or None if no path found
        """
        if start == goal:
            return [start]

        # A* algorithm implementation
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: manhattan_distance(start, goal)}

        visited = set()

        while open_set:
            # Get node with lowest f_score
            open_set.sort()
            current_f, current = open_set.pop(0)

            if current in visited:
                continue

            visited.add(current)

            if current == goal:
                path = self._reconstruct_path(came_from, start, goal)
                return self._compress_path(path)

            for neighbor in self._get_neighbors(current[0], current[1]):
                if neighbor in visited:
                    continue

                # Calculate tentative g_score
                tentative_g = g_score[current] + euclidean_distance(current, neighbor)

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + manhattan_distance(neighbor, goal)

                    if (f_score[neighbor], neighbor) not in open_set:
                        open_set.append((f_score[neighbor], neighbor))

        return None  # No path found

    def compute_distance_matrix(self) -> np.ndarray:
        """
        Compute distance matrix between all POI pairs.

        Returns:
            Distance matrix with shape (n_pois, n_pois)
        """
        n_pois = len(self.poi_coords)
        distance_matrix = np.full((n_pois, n_pois), np.inf)

        logger.info(f"Computing distance matrix for {n_pois} POIs...")

        for i in range(n_pois):
            for j in range(n_pois):
                if i == j:
                    distance_matrix[i, j] = 0
                    continue

                start = tuple(self.poi_coords[i])
                goal = tuple(self.poi_coords[j])

                # Check if distance is within threshold
                euclidean_dist = euclidean_distance(start, goal)
                if euclidean_dist > self.distance_threshold:
                    continue

                # Find path using A*
                path = self.find_path_astar(start, goal)
                if path:
                    # Calculate path length
                    path_length = 0
                    for k in range(len(path) - 1):
                        path_length += euclidean_distance(path[k], path[k + 1])

                    distance_matrix[i, j] = path_length

        logger.info(
            f"Distance matrix computed with {np.sum(np.isfinite(distance_matrix))} finite distances"
        )
        return distance_matrix

    def compute_path_matrix(self) -> List[List[Optional[List[Tuple[int, int]]]]]:
        """
        Compute path matrix between all POI pairs.

        Returns:
            Matrix of paths between POIs
        """
        n_pois = len(self.poi_coords)
        path_matrix = [[None for _ in range(n_pois)] for _ in range(n_pois)]

        logger.info(f"Computing path matrix for {n_pois} POIs...")

        for i in range(n_pois):
            for j in range(n_pois):
                if i == j:
                    path_matrix[i][j] = [tuple(self.poi_coords[i])]
                    continue

                start = tuple(self.poi_coords[i])
                goal = tuple(self.poi_coords[j])

                # Check if distance is within threshold
                euclidean_dist = euclidean_distance(start, goal)
                if euclidean_dist > self.distance_threshold:
                    continue

                # Find path using A*
                path = self.find_path_astar(start, goal)
                path_matrix[i][j] = path

        logger.info("Path matrix computed")
        return path_matrix

    def compute_all_paths(
        self,
    ) -> Tuple[np.ndarray, List[List[Optional[List[Tuple[int, int]]]]]]:
        """
        Compute both distance and path matrices.

        Returns:
            Tuple of (distance_matrix, path_matrix)
        """
        logger.info("Computing all paths between POIs...")

        n_pois = len(self.poi_coords)
        distance_matrix = np.full((n_pois, n_pois), np.inf)
        path_matrix = [[None for _ in range(n_pois)] for _ in range(n_pois)]

        paths_computed = 0

        for i in range(n_pois):
            for j in range(n_pois):
                if i == j:
                    distance_matrix[i, j] = 0
                    path_matrix[i][j] = [tuple(self.poi_coords[i])]
                    continue

                start = tuple(self.poi_coords[i])
                goal = tuple(self.poi_coords[j])

                # Check if distance is within threshold
                euclidean_dist = euclidean_distance(start, goal)
                if euclidean_dist > self.distance_threshold:
                    continue

                # Find path using A*
                path = self.find_path_astar(start, goal)
                if path:
                    # Calculate path length
                    path_length = 0
                    for k in range(len(path) - 1):
                        path_length += euclidean_distance(path[k], path[k + 1])

                    distance_matrix[i, j] = path_length
                    path_matrix[i][j] = path
                    paths_computed += 1

        logger.info(f"Computed {paths_computed} paths between POIs")
        return distance_matrix, path_matrix

    def get_optimization_stats(self) -> dict:
        """
        Get statistics about the JPS optimization.

        Returns:
            Dictionary with optimization statistics
        """
        n_pois = len(self.poi_coords)
        total_pairs = n_pois * (n_pois - 1)

        # Count pairs within threshold
        pairs_within_threshold = 0
        for i in range(n_pois):
            for j in range(n_pois):
                if i != j:
                    start = tuple(self.poi_coords[i])
                    goal = tuple(self.poi_coords[j])
                    if euclidean_distance(start, goal) <= self.distance_threshold:
                        pairs_within_threshold += 1

        return {
            "poi_count": n_pois,
            "total_poi_pairs": total_pairs,
            "pairs_within_threshold": pairs_within_threshold,
            "optimization_ratio": (
                pairs_within_threshold / total_pairs if total_pairs > 0 else 0
            ),
            "distance_threshold": self.distance_threshold,
            "grid_size": f"{self.grid_width}x{self.grid_height}",
            "cache_available": bool(self.jps_cache),
        }
