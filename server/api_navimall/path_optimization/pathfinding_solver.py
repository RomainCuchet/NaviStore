"""
Pathfinding Solver utilisant la librairie pathfinding.

Alternative robuste et fiable à JPS pour le pathfinding dans les layouts de magasin.
Utilise les algorithmes A*, Dijkstra, et autres algorithmes éprouvés.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
import time

try:
    from pathfinding.core.grid import Grid
    from pathfinding.core.diagonal_movement import DiagonalMovement
    from pathfinding.finder.a_star import AStarFinder
    from pathfinding.finder.dijkstra import DijkstraFinder
    from pathfinding.finder.best_first import BestFirst
except ImportError:
    raise ImportError(
        "Librairie pathfinding requise. Installez avec: pip install pathfinding"
    )

from .utils import euclidean_distance, manhattan_distance

logger = logging.getLogger(__name__)


class PathfindingSolver:
    """
    Pathfinding solver using the pathfinding library.

    Supports distance thresholds and performance optimizations.
    """

    def __init__(
        self,
        grid_with_poi: np.ndarray,
        distance_threshold_grid: float,
        poi_coords: np.ndarray,
        algorithm: str = "astar",
        diagonal_movement: bool = True,
    ):
        """
        Initialize pathfinding solver.

        Args:
            grid_with_poi: Grid with POIs marked (0=walkable, 1=POI, -1=obstacle)
            distance_threshold_grid: Distance threshold in grid units
            poi_coords: POI coordinates in grid space
            algorithm: Algorithm to use ('astar', 'dijkstra', 'best_first')
            diagonal_movement: Allow diagonal movements
        """
        self.grid_array = grid_with_poi
        self.distance_threshold = distance_threshold_grid
        self.poi_coords = poi_coords
        self.grid_height, self.grid_width = grid_with_poi.shape
        self.algorithm = algorithm
        self.diagonal_movement = diagonal_movement

        self._create_finder()

        self.stats = {
            "paths_computed": 0,
            "paths_failed": 0,
            "total_computation_time": 0.0,
            "average_path_length": 0.0,
            "algorithm_used": algorithm,
            "diagonal_enabled": diagonal_movement,
        }

        logger.info(
            f"Initialized PathfindingSolver with {len(poi_coords)} POIs, "
            f"threshold={distance_threshold_grid:.2f}, algorithm={algorithm}"
        )

    def _create_finder(self):
        """Crée le finder pathfinding selon l'algorithme choisi."""
        diagonal_mode = (
            DiagonalMovement.always
            if self.diagonal_movement
            else DiagonalMovement.never
        )

        if self.algorithm == "astar":
            self.finder = AStarFinder(diagonal_movement=diagonal_mode)
        elif self.algorithm == "dijkstra":
            self.finder = DijkstraFinder(diagonal_movement=diagonal_mode)
        elif self.algorithm == "best_first":
            self.finder = BestFirst(diagonal_movement=diagonal_mode)
        else:
            raise ValueError(f"Algorithme non supporté: {self.algorithm}")

        logger.debug(
            f"Created {self.algorithm} finder with diagonal={self.diagonal_movement}"
        )

    def find_path(
        self, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Find a path between two points.

        Args:
            start: Starting point (x, y)
            goal: End point (x, y)

        Returns:
            List of path coordinates or None if no path found
        """
        try:
            start_time = time.time()

            # Create a new grid for each search (clone() method doesn't exist)
            # Recreate grid with same data
            walkable_matrix = (self.grid_array >= 0).astype(int)
            grid = Grid(matrix=walkable_matrix)

            # Get start and goal nodes
            # NOTE: pathfinding lib uses node(x, y) where x=col, y=row
            # Our coordinates are (row, col), so we need to swap
            start_node = grid.node(start[1], start[0])  # (col, row)
            goal_node = grid.node(goal[1], goal[0])  # (col, row)

            # Check if nodes are walkable
            if not start_node.walkable or not goal_node.walkable:
                logger.debug(f"Start {start} or goal {goal} not walkable")
                return None

            # Find path
            path, runs = self.finder.find_path(start_node, goal_node, grid)

            computation_time = time.time() - start_time
            self.stats["total_computation_time"] += computation_time

            if path:
                # Convert to list of tuples (row, col)
                # NOTE: node.x=col, node.y=row, so we need to swap
                path_coords = [(node.y, node.x) for node in path]  # (row, col)
                self.stats["paths_computed"] += 1

                # Update average path length
                total_paths = self.stats["paths_computed"]
                current_avg = self.stats["average_path_length"]
                new_length = len(path_coords)
                self.stats["average_path_length"] = (
                    current_avg * (total_paths - 1) + new_length
                ) / total_paths

                logger.debug(
                    f"Path found: {start} -> {goal}, length={len(path_coords)}, "
                    f"time={computation_time:.4f}s"
                )
                return path_coords
            else:
                self.stats["paths_failed"] += 1
                logger.debug(f"No path found: {start} -> {goal}")
                return None

        except Exception as e:
            logger.error(f"Erreur lors du pathfinding {start} -> {goal}: {e}")
            self.stats["paths_failed"] += 1
            return None

    def compute_all_paths(
        self,
    ) -> Tuple[np.ndarray, List[List[Optional[List[Tuple[int, int]]]]]]:
        """
        Compute all distances and paths between POIs.

        Returns:
            Tuple of (distance_matrix, path_matrix)
        """
        logger.info(f"Computing all paths with {self.algorithm.upper()} pathfinding...")
        start_time = time.time()

        n_pois = len(self.poi_coords)
        distance_matrix = np.full((n_pois, n_pois), np.inf)
        path_matrix = [[None for _ in range(n_pois)] for _ in range(n_pois)]

        paths_computed = 0
        paths_failed = 0
        paths_skipped_threshold = 0

        for i in range(n_pois):
            for j in range(n_pois):
                if i == j:
                    # Distance à soi-même = 0
                    distance_matrix[i, j] = 0
                    path_matrix[i][j] = [tuple(self.poi_coords[i])]
                    continue

                start = tuple(self.poi_coords[i])
                goal = tuple(self.poi_coords[j])

                # Check euclidian distance threshold
                euclidean_dist = euclidean_distance(start, goal)
                if euclidean_dist > self.distance_threshold:
                    paths_skipped_threshold += 1
                    logger.debug(
                        f"Skipping {start} -> {goal}: distance {euclidean_dist:.2f} > threshold {self.distance_threshold:.2f}"
                    )
                    distance_matrix[i, j] = euclidean_dist * 3
                    continue

                # Find path
                path = self.find_path(start, goal)

                if path:
                    # Compute the real length of the path
                    path_length = 0
                    for k in range(len(path) - 1):
                        path_length += euclidean_distance(path[k], path[k + 1])

                    distance_matrix[i, j] = path_length
                    path_matrix[i][j] = path
                    paths_computed += 1
                else:
                    paths_failed += 1

        total_time = time.time() - start_time

        logger.info(
            f"{self.algorithm.upper()} pathfinding completed: "
            f"{paths_computed} paths found, {paths_failed} failed, "
            f"{paths_skipped_threshold} skipped (threshold), "
            f"total_time={total_time:.3f}s"
        )

        # Mettre à jour les statistiques globales
        self.stats["total_paths_computed"] = paths_computed
        self.stats["total_paths_failed"] = paths_failed
        self.stats["paths_skipped_threshold"] = paths_skipped_threshold
        self.stats["total_algorithm_time"] = total_time

        return distance_matrix, path_matrix

    def get_optimization_stats(self) -> Dict:
        """
        Returns optimisation statistics
        Retourne les statistiques d'optimisation.
        """
        total_paths = self.stats["paths_computed"] + self.stats["paths_failed"]
        success_rate = (
            self.stats["paths_computed"] / total_paths if total_paths > 0 else 0
        )

        return {
            "algorithm": self.algorithm,
            "diagonal_movement": self.diagonal_movement,
            "grid_size": f"{self.grid_width}x{self.grid_height}",
            "total_pois": len(self.poi_coords),
            "distance_threshold": self.distance_threshold,
            "paths_computed": self.stats.get("total_paths_computed", 0),
            "paths_failed": self.stats.get("total_paths_failed", 0),
            "paths_skipped_threshold": self.stats.get("paths_skipped_threshold", 0),
            "success_rate": f"{success_rate:.2%}",
            "average_path_length": f"{self.stats['average_path_length']:.2f}",
            "total_computation_time": f"{self.stats['total_computation_time']:.3f}s",
            "total_algorithm_time": f"{self.stats.get('total_algorithm_time', 0):.3f}s",
        }

    def get_pathfinding_info(self) -> Dict:
        """Returns detailed information about the solver."""
        return {
            "solver_type": "pathfinding_library",
            "algorithm": self.algorithm,
            "version": "pathfinding2",
            "features": {
                "diagonal_movement": self.diagonal_movement,
                "algorithms_available": ["astar", "dijkstra", "best_first"],
                "distance_thresholding": True,
                "grid_validation": True,
                "performance_stats": True,
            },
            "grid_info": {
                "width": self.grid_width,
                "height": self.grid_height,
                "total_cells": self.grid_width * self.grid_height,
                "walkable_cells": int(np.sum(self.grid_array != -1)),
                "obstacle_cells": int(np.sum(self.grid_array == -1)),
            },
        }


class PathfindingSolverFactory:
    """Factory to create pathfinding solvers with different algorithms."""

    @staticmethod
    def create_solver(
        grid_with_poi: np.ndarray,
        distance_threshold_grid: float,
        poi_coords: np.ndarray,
        algorithm: str = "astar",
        diagonal_movement: bool = True,
    ) -> PathfindingSolver:
        """
        Crée un solver pathfinding.

        Args:
            grid_with_poi: Grille avec POIs
            distance_threshold_grid: Seuil de distance
            poi_coords: Coordonnées POIs
            algorithm: Algorithme ('astar', 'dijkstra', 'best_first')
            diagonal_movement: Autoriser diagonales

        Returns:
            PathfindingSolver configuré
        """
        return PathfindingSolver(
            grid_with_poi=grid_with_poi,
            distance_threshold_grid=distance_threshold_grid,
            poi_coords=poi_coords,
            algorithm=algorithm,
            diagonal_movement=diagonal_movement,
        )

    @staticmethod
    def get_available_algorithms() -> List[str]:
        """Returns the list of available algorithms."""
        return ["astar", "dijkstra", "best_first"]

    @staticmethod
    def get_recommended_algorithm(grid_size: int, poi_count: int) -> str:
        """
        Recommends an algorithm based on grid size and POI count.

        Args:
            grid_size: Grid size (width * height)
            poi_count: Number of POIs

        Returns:
            Name of recommended algorithm
        """
        if grid_size > 10000 and poi_count > 20:
            return "best_first"  # Faster for large grid
        elif poi_count > 50:
            return "dijkstra"  # Better for large number of POI
        else:
            return "astar"  # Best in most cases
