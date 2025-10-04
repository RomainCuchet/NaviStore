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

    Reconstructs full path from TSP visiting order and JPS computed paths.
    """

    def __init__(
        self,
        path_matrix: List[List[Optional[List[Tuple[int, int]]]]],
        visiting_order: List[int],
        poi_coords: np.ndarray,
    ):
        """
        Initialize the final path generator.

        Args:
            path_matrix: Matrix of paths between POIs from PathfindingSolver
            visiting_order: Optimal visiting order from TSPSolver
            poi_coords: Array of POI coordinates in grid space
        """
        self.path_matrix = path_matrix
        self.visiting_order = visiting_order
        self.poi_coords = poi_coords
        self.n_pois = len(poi_coords)

        logger.info(f"Initialized FinalPathGenerator for {len(visiting_order)} POIs")

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

    def _get_path_between_pois(
        self, from_poi: int, to_poi: int
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Get path between two POIs from the path matrix.

        Args:
            from_poi: Source POI index
            to_poi: Destination POI index

        Returns:
            Path between POIs or None if no path exists
        """
        if from_poi == to_poi:
            return [tuple(self.poi_coords[from_poi])]

        path = self.path_matrix[from_poi][to_poi]
        if path is None:
            logger.warning(f"No path found between POI {from_poi} and POI {to_poi}")

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
                # Fallback: direct line to POI coordinate
                logger.warning(
                    f"Using direct path from POI {current_poi} to POI {next_poi}"
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
            Dictionary with path summary
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
        }
