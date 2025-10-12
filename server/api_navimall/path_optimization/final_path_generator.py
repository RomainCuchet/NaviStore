"""
Final Path Generator for reconstructing complete shopping paths.

Generates the final traversable path from TSP solution and JPS paths.
"""

import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FinalPathGenerator:
    """
    Generates the final complete path for shopping route execution.

    Reconstructs full path from TSP visiting order and computed paths.
    Includes A* fallback for missing path segments.
    """

    def __init__(
        self,
        path_matrix: List[List[Optional[List[Tuple[int, int]]]]],
        visiting_order: List[int],
        poi_coords: np.ndarray,
        grid_with_poi: Optional[np.ndarray] = None,
        pathfinding_algorithm: str = "astar",
        diagonal_movement: bool = False,
    ):
        """
        Initialize the final path generator.

        Args:
            path_matrix: Matrix of paths between POIs from PathfindingSolver
            visiting_order: Optimal visiting order from TSPSolver
            poi_coords: Array of POI coordinates in grid space
            grid_with_poi: Grid layout for fallback pathfinding (optional)
            pathfinding_algorithm: Algorithm for fallback pathfinding
            diagonal_movement: Allow diagonal movement in fallback pathfinding
        """
        self.path_matrix = path_matrix
        self.visiting_order = visiting_order
        self.poi_coords = poi_coords
        self.n_pois = len(poi_coords)

        # Fallback pathfinding configuration
        self.grid_with_poi = grid_with_poi
        self.pathfinding_algorithm = pathfinding_algorithm
        self.diagonal_movement = diagonal_movement

        # Statistics for fallback usage
        self.fallback_stats = {
            "fallback_calls": 0,
            "fallback_successes": 0,
            "fallback_failures": 0,
        }

        logger.info(
            f"Initialized FinalPathGenerator for {len(visiting_order)} POIs with fallback={'enabled' if grid_with_poi is not None else 'disabled'}"
        )

    def _validate_inputs(self) -> None:
        """
        Validate input parameters.

        Raises:
            ValueError: If inputs are invalid
        """
        if len(self.visiting_order) != self.n_pois:
            raise ValueError(
                f"Visiting order length ({len(self.visiting_order)}) "
                f"must match number of POIs ({self.n_pois})"
            )

        # Check that all POI indices in visiting order are valid
        for poi_idx in self.visiting_order:
            if poi_idx < 0 or poi_idx >= self.n_pois:
                raise ValueError(f"Invalid POI index {poi_idx} in visiting order")

        # Check that path matrix has correct dimensions
        if len(self.path_matrix) != self.n_pois:
            raise ValueError(
                f"Path matrix rows ({len(self.path_matrix)}) "
                f"must match number of POIs ({self.n_pois})"
            )

        for i, row in enumerate(self.path_matrix):
            if len(row) != self.n_pois:
                raise ValueError(
                    f"Path matrix row {i} has {len(row)} columns, "
                    f"expected {self.n_pois}"
                )

    def _fallback_pathfinding(
        self, from_poi: int, to_poi: int
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Fallback pathfinding using A* when no cached path is available.

        Args:
            from_poi: Source POI index
            to_poi: Destination POI index

        Returns:
            Computed path or None if pathfinding fails
        """
        if self.grid_with_poi is None:
            logger.warning(
                f"No grid available for fallback pathfinding {from_poi} -> {to_poi}"
            )
            return None

        self.fallback_stats["fallback_calls"] += 1

        try:
            # Import PathfindingSolver locally to avoid circular imports
            from .pathfinding_solver import PathfindingSolver

            start = tuple(self.poi_coords[from_poi])
            goal = tuple(self.poi_coords[to_poi])

            logger.info(
                f"Fallback A* pathfinding: POI {from_poi} {start} -> POI {to_poi} {goal}"
            )

            # Create temporary solver with infinite threshold for fallback
            fallback_solver = PathfindingSolver(
                grid_with_poi=self.grid_with_poi,
                distance_threshold_grid=float("inf"),  # No distance limit for fallback
                poi_coords=np.array([start, goal]),
                algorithm=self.pathfinding_algorithm,
                diagonal_movement=self.diagonal_movement,
            )

            # Calculate path using A*
            path = fallback_solver.find_path(start, goal)

            if path is not None:
                self.fallback_stats["fallback_successes"] += 1
                logger.info(f"Fallback A* found path: {len(path)} points")

                # Cache the computed path for future use
                self.path_matrix[from_poi][to_poi] = path

                return path
            else:
                self.fallback_stats["fallback_failures"] += 1
                logger.warning(f"Fallback A* failed: no path {from_poi} -> {to_poi}")
                return None

        except Exception as e:
            self.fallback_stats["fallback_failures"] += 1
            logger.error(f"Fallback pathfinding error {from_poi} -> {to_poi}: {e}")
            return None

    def _get_path_between_pois(
        self, from_poi: int, to_poi: int
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Get path between two POIs from the path matrix with A* fallback.

        Args:
            from_poi: Source POI index
            to_poi: Destination POI index

        Returns:
            Path between POIs, computed from cache or A* fallback
        """
        if from_poi == to_poi:
            return [tuple(self.poi_coords[from_poi])]

        # Try to get cached path first
        path = self.path_matrix[from_poi][to_poi]

        if path is None:
            logger.warning(
                f"No cached path between POI {from_poi} and POI {to_poi}, trying fallback A*"
            )

            # Attempt fallback pathfinding
            fallback_path = self._fallback_pathfinding(from_poi, to_poi)

            if fallback_path is not None:
                logger.info(
                    f"Fallback A* successfully computed path {from_poi} -> {to_poi}"
                )
                return fallback_path
            else:
                logger.error(
                    f"Both cached and fallback pathfinding failed {from_poi} -> {to_poi}"
                )
                return None

        return path

    def generate_complete_path(
        self, include_return_to_start: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Generate the complete shopping path following the visiting order.

        Args:
            include_return_to_start: Whether to include return path to starting POI

        Returns:
            Complete path as list of grid coordinates

        Raises:
            ValueError: If path generation fails
        """
        self._validate_inputs()

        if len(self.visiting_order) == 0:
            return []

        if len(self.visiting_order) == 1:
            return [tuple(self.poi_coords[self.visiting_order[0]])]

        complete_path = []

        # Add segments between consecutive POIs
        for i in range(len(self.visiting_order) - 1):
            current_poi = self.visiting_order[i]
            next_poi = self.visiting_order[i + 1]

            segment_path = self._get_path_between_pois(current_poi, next_poi)

            if segment_path is None:
                # Last resort: direct line to POI coordinate
                logger.error(
                    f"No path available between POI {current_poi} and POI {next_poi}, using direct connection"
                )
                if not complete_path:
                    complete_path.append(tuple(self.poi_coords[current_poi]))
                complete_path.append(tuple(self.poi_coords[next_poi]))
            else:
                # Add segment, avoiding duplicate points
                if not complete_path:
                    complete_path.extend(segment_path)
                else:
                    # Skip first point to avoid duplication
                    complete_path.extend(segment_path[1:])

        # Optionally add return path to start
        if include_return_to_start and len(self.visiting_order) > 1:
            start_poi = self.visiting_order[0]
            end_poi = self.visiting_order[-1]

            return_path = self._get_path_between_pois(end_poi, start_poi)
            if return_path is not None and len(return_path) > 1:
                complete_path.extend(return_path[1:])  # Skip duplicate point

        logger.info(f"Generated complete path with {len(complete_path)} points")
        return complete_path

    def generate_path_grid(self, grid_shape: Tuple[int, int]) -> np.ndarray:
        """
        Generate a grid representation of the traversed path.

        Args:
            grid_shape: Shape of the output grid (height, width)

        Returns:
            Grid array with path marked (0=empty, 1=path, 2=POI)
        """
        height, width = grid_shape
        path_grid = np.zeros((height, width), dtype=int)

        # Generate complete path
        complete_path = self.generate_complete_path()

        # Mark path points
        for x, y in complete_path:
            if 0 <= x < width and 0 <= y < height:
                path_grid[y, x] = 1  # Mark as path

        # Mark POI locations
        for poi_idx in self.visiting_order:
            x, y = self.poi_coords[poi_idx]
            if 0 <= x < width and 0 <= y < height:
                path_grid[y, x] = 2  # Mark as POI

        logger.info(f"Generated path grid with shape {grid_shape}")
        return path_grid

    def get_segment_info(self) -> List[dict]:
        """
        Get detailed information about each path segment.

        Returns:
            List of segment information dictionaries
        """
        self._validate_inputs()

        segments = []

        for i in range(len(self.visiting_order) - 1):
            current_poi = self.visiting_order[i]
            next_poi = self.visiting_order[i + 1]

            segment_path = self._get_path_between_pois(current_poi, next_poi)

            segment_info = {
                "segment_index": i,
                "from_poi": current_poi,
                "to_poi": next_poi,
                "from_coords": tuple(self.poi_coords[current_poi]),
                "to_coords": tuple(self.poi_coords[next_poi]),
                "path_available": segment_path is not None,
                "path_length": len(segment_path) if segment_path else 0,
                "path_points": segment_path,
            }

            segments.append(segment_info)

        return segments

    def calculate_total_distance(self) -> float:
        """
        Calculate total distance of the complete path.

        Returns:
            Total path distance in grid units
        """
        complete_path = self.generate_complete_path()

        if len(complete_path) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(len(complete_path) - 1):
            p1 = complete_path[i]
            p2 = complete_path[i + 1]

            # Calculate Euclidean distance
            distance = np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
            total_distance += distance

        return total_distance

    def get_path_summary(self) -> dict:
        """
        Get summary information about the generated path.

        Returns:
            Dictionary with path summary including fallback statistics
        """
        complete_path = self.generate_complete_path()

        return {
            "total_pois": len(self.visiting_order),
            "visiting_order": self.visiting_order,
            "total_path_points": len(complete_path),
            "total_distance": self.calculate_total_distance(),
            "segments_count": (
                len(self.visiting_order) - 1 if len(self.visiting_order) > 1 else 0
            ),
            "start_poi": self.visiting_order[0] if self.visiting_order else None,
            "end_poi": self.visiting_order[-1] if self.visiting_order else None,
            "start_coords": (
                tuple(self.poi_coords[self.visiting_order[0]])
                if self.visiting_order
                else None
            ),
            "end_coords": (
                tuple(self.poi_coords[self.visiting_order[-1]])
                if self.visiting_order
                else None
            ),
            "fallback_pathfinding": self.fallback_stats,
        }

    def get_fallback_stats(self) -> dict:
        """
        Get detailed fallback pathfinding statistics.

        Returns:
            Dictionary with fallback statistics
        """
        total_calls = self.fallback_stats["fallback_calls"]
        success_rate = (
            self.fallback_stats["fallback_successes"] / total_calls
            if total_calls > 0
            else 0
        )

        return {
            "fallback_calls": total_calls,
            "fallback_successes": self.fallback_stats["fallback_successes"],
            "fallback_failures": self.fallback_stats["fallback_failures"],
            "fallback_success_rate": f"{success_rate:.2%}",
            "fallback_enabled": self.grid_with_poi is not None,
            "fallback_algorithm": self.pathfinding_algorithm,
        }
