"""
Store Layout Cache Manager for JPS optimization.

Handles version management and JPS cache generation based on store layout changes.
"""

import numpy as np
import xxhash
import pickle
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StoreLayoutCacheManager:
    """
    Manages JPS cache generation and versioning based on store layout changes.

    Uses XXH3 64-bit hash to detect layout changes and regenerate cache when needed.
    """

    def __init__(
        self,
        layout: np.ndarray,
        previous_hash: Optional[str] = None,
        cache_dir: str = "cache",
    ):
        """
        Initialize the cache manager.

        Args:
            layout: Numpy array representing the store layout
            previous_hash: Previously computed hash for comparison
            cache_dir: Directory to store cache files
        """
        self.layout = layout
        self.previous_hash = previous_hash
        self.cache_dir = cache_dir
        self.current_hash = self._compute_layout_hash()

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        logger.info(f"Initialized cache manager. Current hash: {self.current_hash}")

    def _compute_layout_hash(self) -> str:
        """
        Compute XXH3 64-bit hash of the current store layout.

        Returns:
            Hexadecimal string representation of the hash
        """
        # Convert numpy array to bytes for hashing
        layout_bytes = self.layout.tobytes()

        # Compute XXH3 64-bit hash
        hash_value = xxhash.xxh3_64(layout_bytes)
        hash_hex = hash_value.hexdigest()

        logger.debug(f"Computed layout hash: {hash_hex}")
        return hash_hex

    def needs_cache_update(self) -> bool:
        """
        Check if cache needs to be updated based on hash comparison.

        Returns:
            True if cache needs update, False otherwise
        """
        if self.previous_hash is None:
            logger.info("No previous hash found, cache update needed")
            return True

        needs_update = self.current_hash != self.previous_hash

        if needs_update:
            logger.info(
                f"Layout changed (prev: {self.previous_hash}, curr: {self.current_hash}), cache update needed"
            )
        else:
            logger.info("Layout unchanged, cache update not needed")

        return needs_update

    def get_cache_filename(self, extension: str = "pkl") -> str:
        """
        Generate cache filename based on current hash.

        Args:
            extension: File extension for cache file

        Returns:
            Cache filename with format: <hash>.<extension>
        """
        return os.path.join(self.cache_dir, f"{self.current_hash}.{extension}")

    def generate_jps_cache(self, grid_with_poi: np.ndarray) -> dict:
        """
        Generate JPS jump point cache optimized for the grid.

        Args:
            grid_with_poi: Grid with points of interest marked

        Returns:
            Dictionary containing JPS cache data
        """
        logger.info("Generating JPS jump point cache...")

        # This is a simplified JPS cache generation
        # In a real implementation, this would compute jump points for all grid positions
        cache_data = {
            "hash": self.current_hash,
            "grid_shape": grid_with_poi.shape,
            "jump_points": self._compute_jump_points(grid_with_poi),
            "metadata": {
                "generation_timestamp": np.datetime64("now").astype(str),
                "grid_size": grid_with_poi.size,
                "obstacle_count": np.sum(grid_with_poi == -1),
            },
        }

        logger.info(
            f"Generated JPS cache with {len(cache_data['jump_points'])} jump points"
        )
        return cache_data

    def _compute_jump_points(self, grid: np.ndarray) -> dict:
        """
        Compute jump points for JPS optimization.

        Args:
            grid: The grid layout

        Returns:
            Dictionary mapping grid positions to jump points
        """
        jump_points = {}
        height, width = grid.shape

        # Simplified jump point computation
        # Real implementation would use proper JPS algorithm
        for y in range(height):
            for x in range(width):
                if grid[y, x] != -1:  # Not an obstacle
                    # Compute jump points in all 8 directions
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

                    point_jumps = {}
                    for dx, dy in directions:
                        jump_point = self._find_jump_point(grid, x, y, dx, dy)
                        if jump_point:
                            point_jumps[f"{dx},{dy}"] = jump_point

                    if point_jumps:
                        jump_points[f"{x},{y}"] = point_jumps

        return jump_points

    def _find_jump_point(
        self, grid: np.ndarray, start_x: int, start_y: int, dx: int, dy: int
    ) -> Optional[tuple]:
        """
        Find jump point in a specific direction from start position.

        Args:
            grid: The grid layout
            start_x, start_y: Starting position
            dx, dy: Direction vector

        Returns:
            Jump point coordinates or None if no jump point found
        """
        height, width = grid.shape
        x, y = start_x + dx, start_y + dy

        # Simple jump point detection (simplified)
        steps = 0
        max_steps = max(width, height)

        while (
            0 <= x < width
            and 0 <= y < height
            and grid[y, x] != -1
            and steps < max_steps
        ):

            # Check if this is a jump point (forced neighbor detection)
            if self._is_jump_point(grid, x, y, dx, dy):
                return (x, y)

            x += dx
            y += dy
            steps += 1

        return None

    def _is_jump_point(
        self, grid: np.ndarray, x: int, y: int, dx: int, dy: int
    ) -> bool:
        """
        Check if a position is a jump point.

        Args:
            grid: The grid layout
            x, y: Position to check
            dx, dy: Direction we came from

        Returns:
            True if this is a jump point
        """
        height, width = grid.shape

        # Simplified jump point detection
        # Real JPS would check for forced neighbors

        # Check for obstacles that would force this to be a jump point
        if dx != 0 and dy != 0:  # Diagonal movement
            # Check for forced neighbors in diagonal movement
            if (
                0 <= x - dx < width
                and 0 <= y < height
                and grid[y, x - dx] == -1
                and 0 <= x - dx < width
                and 0 <= y + dy < height
                and grid[y + dy, x - dx] != -1
            ):
                return True

        return False

    def save_cache(self, cache_data: dict) -> str:
        """
        Save JPS cache to file.

        Args:
            cache_data: Cache data to save

        Returns:
            Path to saved cache file
        """
        cache_filename = self.get_cache_filename()

        with open(cache_filename, "wb") as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info(f"Saved JPS cache to {cache_filename}")
        return cache_filename

    def load_cache(self) -> Optional[dict]:
        """
        Load JPS cache from file.

        Returns:
            Cache data or None if file doesn't exist
        """
        cache_filename = self.get_cache_filename()

        if not os.path.exists(cache_filename):
            logger.debug(f"Cache file {cache_filename} not found")
            return None

        try:
            with open(cache_filename, "rb") as f:
                cache_data = pickle.load(f)

            logger.info(f"Loaded JPS cache from {cache_filename}")
            return cache_data

        except Exception as e:
            logger.error(f"Error loading cache file {cache_filename}: {str(e)}")
            return None

    def update_cache_if_needed(self, grid_with_poi: np.ndarray) -> tuple:
        """
        Update cache if needed and return current hash and cache data.

        Args:
            grid_with_poi: Grid with points of interest

        Returns:
            Tuple of (current_hash, cache_data)
        """
        # Try to load existing cache
        cache_data = self.load_cache()

        if self.needs_cache_update() or cache_data is None:
            # Generate new cache
            cache_data = self.generate_jps_cache(grid_with_poi)
            self.save_cache(cache_data)
            logger.info("Cache updated successfully")
        else:
            logger.info("Using existing cache")

        return self.current_hash, cache_data

    def get_current_hash(self) -> str:
        """
        Get the current layout hash.

        Returns:
            Current XXH3 hash string
        """
        return self.current_hash
