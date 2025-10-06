"""
Store Layout Manager.

Handles version management and SVG generation based on store layout changes.
"""

import numpy as np
import xxhash
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StoreLayoutManager:
    """
    Manages store layout SVG generation based on layout changes.

    Uses XXH3 64-bit hash to detect layout changes and generate SVG assets when needed.
    """

    def __init__(
        self,
        layout: np.ndarray,
        previous_hash: Optional[str] = None,
        svg_assets_dir: str = "assets/svg",
    ):
        """
        Initialize the layout manager.

        Args:
            layout: Numpy array representing the store layout
            previous_hash: Previously computed hash for comparison
            svg_assets_dir: Directory to store SVG assets
        """
        self.layout = layout
        self.previous_hash = previous_hash
        self.current_hash = self._compute_layout_hash()
        self.svg_assets_dir = svg_assets_dir

        # Ensure SVG assets directory exists
        os.makedirs(self.svg_assets_dir, exist_ok=True)

        logger.info(
            f"Initialized StoreLayoutManager. Current hash: {self.current_hash}"
        )

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

    def needs_svg_update(self) -> bool:
        """
        Check if store_layout SVG asset needs to be updated based on hash comparison.

        Returns:
            True if SVG needs update, False otherwise
        """
        if self.previous_hash is None:
            logger.info("No previous hash found, SVG update needed")
            return True

        needs_update = self.current_hash != self.previous_hash

        if needs_update:
            logger.info(
                f"Layout changed (prev: {self.previous_hash}, curr: {self.current_hash}), SVG update needed"
            )
        else:
            logger.info("Layout unchanged, SVG update not needed")

        return needs_update

    def get_svg_filename(self) -> str:
        """
        Generate SVG filename based on current hash.

        Returns:
            SVG filename with format: <hash>.svg
        """
        return os.path.join(self.svg_assets_dir, f"{self.current_hash}.svg")

    def generate_svg_layout(self) -> str:
        """
        Generate SVG representation of the store layout.

        Returns:
            Path to generated SVG file
        """
        svg_filename = self.get_svg_filename()

        logger.info(f"Generating SVG layout: {svg_filename}")

        # TODO: Implement SVG generation logic
        # This should create an SVG representation of self.layout
        # - Convert numpy array to SVG format
        # - Use different colors/styles for obstacles, walkable areas, POIs
        # - Save to svg_filename
        # - Return the path to the generated file

        logger.info(f"SVG layout generated: {svg_filename}")
        return svg_filename

    def update_svg_if_needed(self) -> tuple:
        """
        Update SVG if needed and return current hash and SVG path.

        Returns:
            Tuple of (current_hash, svg_path)
        """
        svg_path = self.get_svg_filename()

        if self.needs_svg_update() or not os.path.exists(svg_path):
            # Generate new SVG
            svg_path = self.generate_svg_layout()
            logger.info("SVG updated successfully")
        else:
            logger.info("Using existing SVG")

        return self.current_hash, svg_path

    def get_current_hash(self) -> str:
        """
        Get the current layout hash.

        Returns:
            Current XXH3 hash string
        """
        return self.current_hash
