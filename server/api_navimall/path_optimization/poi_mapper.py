"""
Point of Interest Mapper for JPS-TSP optimization.

Handles transformation of real-world coordinates to grid indices and POI integration.
"""

import numpy as np
from typing import List, Tuple
import logging

from .utils import real_world_to_grid_coords

logger = logging.getLogger(__name__)


class POIMapper:
    """
    Maps points of interest from real-world coordinates to grid indices.

    Transforms coordinates, validates placement, and integrates POIs into the grid.
    """

    def __init__(
        self,
        layout: np.ndarray,
        distance_threshold: float,
        real_world_coords: List[Tuple[float, float]],
        edge_length: float,
    ):
        """
        Initialize the POI mapper.

        Args:
            layout: Original store layout numpy array
            distance_threshold: Distance threshold in real-world units
            real_world_coords: List of POI coordinates in real-world frame
            edge_length: Size of one grid cell in centimeters
        """
        self.original_layout = layout.copy()
        self.distance_threshold = distance_threshold
        self.real_world_coords = np.array(real_world_coords)
        self.edge_length = edge_length

        logger.info(
            f"Initialized POI mapper with {len(real_world_coords)} POIs, "
            f"threshold={distance_threshold}, edge_length={edge_length}cm"
        )

    def _validate_grid_bounds(self, grid_coords: np.ndarray) -> None:
        """
        Validate that grid coordinates are within bounds.
        Note: x=row (vertical), y=col (horizontal), origin at top-left

        Args:
            grid_coords: Array of grid coordinates to validate

        Raises:
            ValueError: If any coordinates are out of bounds
        """
        height, width = self.original_layout.shape

        # Check bounds - x=row, y=col
        x_coords, y_coords = grid_coords[:, 0], grid_coords[:, 1]

        if np.any(x_coords < 0) or np.any(x_coords >= height):
            raise ValueError(f"POI x-coordinates (rows) out of bounds [0, {height-1}]")

        if np.any(y_coords < 0) or np.any(y_coords >= width):
            raise ValueError(f"POI y-coordinates (cols) out of bounds [0, {width-1}]")

    def _check_obstacle_conflicts(self, grid_coords: np.ndarray) -> None:
        """
        Check if any POI coordinates conflict with obstacles.
        Note: x=row (vertical), y=col (horizontal), origin at top-left

        Args:
            grid_coords: Array of grid coordinates to check

        Raises:
            ValueError: If any POI conflicts with an obstacle
        """
        for i, (x, y) in enumerate(grid_coords):
            if self.original_layout[x, y] == -1:  # matrix[row, col]
                real_coord = self.real_world_coords[i]
                raise ValueError(
                    f"POI at real-world coordinates {real_coord} "
                    f"(grid: row={x}, col={y}) conflicts with an obstacle"
                )

    def transform_coordinates(self) -> np.ndarray:
        """
        Transform real-world coordinates to grid indices.

        Returns:
            Array of grid coordinates with shape (N, 2)

        Raises:
            ValueError: If coordinates are invalid or conflict with obstacles
        """
        if len(self.real_world_coords) == 0:
            return np.array([]).reshape(0, 2)

        # Convert to grid coordinates
        grid_coords = real_world_to_grid_coords(
            self.real_world_coords, self.edge_length
        )

        # Validate coordinates
        self._validate_grid_bounds(grid_coords)
        self._check_obstacle_conflicts(grid_coords)

        logger.info(f"Transformed {len(grid_coords)} POI coordinates to grid space")
        return grid_coords

    def compute_distance_threshold_grid(self) -> float:
        """
        Convert distance threshold to grid units.

        Returns:
            Distance threshold in grid units
        """
        threshold_grid = self.distance_threshold / self.edge_length
        logger.debug(
            f"Distance threshold: {self.distance_threshold} -> {threshold_grid} grid units"
        )
        return threshold_grid

    def generate_grid(self) -> Tuple[np.ndarray, float]:
        """
        Generate grid with points of interest and compute grid threshold.

        Returns:
            Tuple of (updated_grid, distance_threshold_grid)

        Raises:
            ValueError: If POI placement is invalid
        """
        # Transform coordinates
        grid_coords = self.transform_coordinates()

        # Create updated grid
        updated_grid = self.original_layout.copy()

        # Mark POIs in the grid
        for x, y in grid_coords:
            updated_grid[x, y] = 1  # Mark as point of interest (x=row, y=col)

        # Compute grid threshold
        distance_threshold_grid = self.compute_distance_threshold_grid()

        poi_count = len(grid_coords)
        logger.info(
            f"Generated grid with {poi_count} POIs, "
            f"threshold={distance_threshold_grid:.2f} grid units"
        )

        return updated_grid, distance_threshold_grid

    def get_poi_grid_coordinates(self) -> np.ndarray:
        """
        Get the grid coordinates of all POIs.

        Returns:
            Array of POI grid coordinates
        """
        return self.transform_coordinates()

    def validate_poi_placement(self) -> bool:
        """
        Validate that all POIs can be placed without conflicts.

        Returns:
            True if all POIs are valid, False otherwise
        """
        try:
            self.transform_coordinates()
            return True
        except ValueError as e:
            logger.warning(f"POI validation failed: {str(e)}")
            return False

    def get_poi_summary(self) -> dict:
        """
        Get summary information about POI mapping.

        Returns:
            Dictionary with POI mapping summary
        """
        try:
            grid_coords = self.transform_coordinates()
            valid = True
            error_message = None
        except ValueError as e:
            grid_coords = np.array([]).reshape(0, 2)
            valid = False
            error_message = str(e)

        return {
            "poi_count": len(self.real_world_coords),
            "valid_placement": valid,
            "error_message": error_message,
            "distance_threshold_real": self.distance_threshold,
            "distance_threshold_grid": self.compute_distance_threshold_grid(),
            "edge_length": self.edge_length,
            "grid_shape": self.original_layout.shape,
            "real_world_coords": self.real_world_coords.tolist(),
            "grid_coords": grid_coords.tolist() if valid else None,
        }
