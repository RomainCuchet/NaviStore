"""
Store Layout Manager.

Handles version management and SVG generation based on store layout changes.
"""

import numpy as np
import xxhash
import os
from typing import Optional, Dict, Tuple
import logging

from fastapi import UploadFile, HTTPException

from api_navimall.layout_svg_generator import generate_svg_from_h5
from .utils import load_layout_from_h5, save_hash_to_json, load_hash_from_json

logger = logging.getLogger(__name__)

DEFAULT_LAYOUTS_DIR = "assets/layouts"
DEFAULT_CACHE_DIR = "assets/cache"
DEFAULT_SVG_DIR = "assets/svg"
DEFAULT_HASH_FILENAME = "current_layout.json"


class StoreLayoutManager:
    """
    Manages store layout SVG generation based on layout changes.

    Uses XXH3 64-bit hash to detect layout changes and generate SVG assets when needed.
    """

    def __init__(
        self,
        layout: np.ndarray,
        previous_hash: Optional[str] = None,
        svg_assets_dir: str = DEFAULT_SVG_DIR,
        layout_path: Optional[str] = None,
        edge_length: Optional[float] = None,
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
        self.svg_assets_dir = svg_assets_dir
        self.layout_path = layout_path
        self.edge_length = edge_length
        self.current_hash = self._compute_layout_hash()
        self.last_svg_updated = False

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

    def get_svg_path(self) -> str:
        """
        Generate SVG filename based on current hash.

        Returns:
            SVG filename with format: <hash>.svg
        """
        return os.path.join(self.svg_assets_dir, f"{self.current_hash}.svg")

    def generate_svg_layout(
        self, layout_path: str, svg_path: str, include_metadata: bool = True
    ) -> None:
        """
        Generate SVG representation of the store layout.

        Args:
            layout_path: Path to the layout HDF5 file
            svg_path: Path to the generated SVG file
            include_metadata: Whether to generate metadata JSON file alongside SVG
        """
        logger.info(f"Generating SVG layout: {svg_path}")

        generate_svg_from_h5(
            layout_path, output_svg_path=svg_path, include_metadata=include_metadata
        )

        logger.info(f"SVG layout generated: {svg_path}")

    def update_svg_if_needed(
        self, layout_path: Optional[str] = None, include_metadata: bool = True
    ) -> Tuple[str, str]:
        """
        Update SVG if needed and return current hash and SVG path.

        Returns:
            Tuple of (current_hash, svg_path)
        """
        svg_path = self.get_svg_path()

        layout_source = layout_path or self.layout_path
        if layout_source is None:
            raise ValueError("Layout path is required to generate SVG assets")

        if self.needs_svg_update() or not os.path.exists(svg_path):
            # Generate new SVG
            self.generate_svg_layout(layout_source, svg_path, include_metadata)
            self.last_svg_updated = True
            logger.info("SVG updated successfully")
        else:
            self.last_svg_updated = False
            logger.info("Using existing SVG")

        return self.current_hash, svg_path

    def get_current_hash(self) -> str:
        """
        Get the current layout hash.

        Returns:
            Current XXH3 hash string
        """
        return self.current_hash

    @staticmethod
    def _ensure_directories(*directories: str) -> None:
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)

    @staticmethod
    def _compute_layout_statistics(layout: np.ndarray) -> Dict[str, int]:
        return {
            "obstacles_count": int((layout == -1).sum()),
            "navigable_cells": int((layout >= 0).sum()),
            "poi_count": int((layout == 1).sum()),
            "shelf_count": int((layout == 2).sum()),
        }

    @staticmethod
    def _hash_file_path(cache_dir: str, hash_filename: str) -> str:
        return os.path.join(cache_dir, hash_filename)

    @classmethod
    async def upload_layout(
        cls,
        layout_file: UploadFile,
        user_info: dict,
        layouts_dir: str = DEFAULT_LAYOUTS_DIR,
        cache_dir: str = DEFAULT_CACHE_DIR,
        svg_dir: str = DEFAULT_SVG_DIR,
        hash_filename: str = DEFAULT_HASH_FILENAME,
    ) -> Dict[str, object]:
        if not layout_file.filename or not layout_file.filename.endswith(".h5"):
            raise HTTPException(
                status_code=422, detail="File must be in HDF5 format (.h5)"
            )

        cls._ensure_directories(layouts_dir, cache_dir, svg_dir)

        temp_path = os.path.join(layouts_dir, f"temp_{layout_file.filename}")
        hash_file_path = cls._hash_file_path(cache_dir, hash_filename)

        try:
            with open(temp_path, "wb") as buffer:
                content = await layout_file.read()
                buffer.write(content)

            try:
                layout, edge_length, _ = load_layout_from_h5(temp_path)
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise HTTPException(
                    status_code=422, detail=f"Invalid HDF5 file: {str(e)}"
                )

            previous_hash = load_hash_from_json(hash_file_path)

            manager = cls(
                layout=layout,
                previous_hash=previous_hash,
                svg_assets_dir=svg_dir,
                layout_path=temp_path,
                edge_length=edge_length,
            )

            logger.info(
                "Received layout upload from user=%s (prev_hash=%s, new_hash=%s)",
                user_info.get("user"),
                previous_hash,
                manager.current_hash,
            )

            layout_stats = cls._compute_layout_statistics(layout)
            layout_shape = tuple(int(v) for v in layout.shape)

            if previous_hash == manager.current_hash:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                logger.info(
                    "Uploaded layout identical to current layout; no update performed"
                )
                return {
                    "success": True,
                    "updated": False,
                    "layout_hash": manager.current_hash,
                    "layout_shape": layout_shape,
                    "edge_length": edge_length,
                    **layout_stats,
                    "message": "Uploaded layout identical to existing layout.",
                }

            permanent_path = os.path.join(layouts_dir, f"{manager.current_hash}.h5")
            if os.path.exists(permanent_path):
                os.remove(permanent_path)
            os.rename(temp_path, permanent_path)

            save_hash_to_json(manager.current_hash, hash_file_path)

            manager.layout_path = permanent_path
            current_hash, svg_path = manager.update_svg_if_needed(permanent_path)

            response: Dict[str, object] = {
                "success": True,
                "updated": True,
                "layout_hash": current_hash,
                "layout_shape": layout_shape,
                "edge_length": edge_length,
                **layout_stats,
                "svg_path": svg_path,
                "message": "Layout updated successfully.",
            }

            if previous_hash:
                response["previous_hash"] = previous_hash

            response["svg_updated"] = manager.last_svg_updated
            logger.info(
                "Layout updated (user=%s, hash=%s, svg_updated=%s)",
                user_info.get("user"),
                current_hash,
                manager.last_svg_updated,
            )
            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Layout upload error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @classmethod
    def get_current_layout_hash_info(
        cls,
        cache_dir: str = DEFAULT_CACHE_DIR,
        hash_filename: str = DEFAULT_HASH_FILENAME,
    ) -> Dict[str, object]:
        hash_file_path = cls._hash_file_path(cache_dir, hash_filename)
        current_hash = load_hash_from_json(hash_file_path)

        if not current_hash:
            return {
                "success": False,
                "layout_hash": None,
                "hash_file": hash_file_path,
                "message": "No store layout uploaded yet.",
            }

        return {
            "success": True,
            "layout_hash": current_hash,
            "hash_file": hash_file_path,
        }

    @classmethod
    def get_current_svg_info(
        cls,
        svg_dir: str = DEFAULT_SVG_DIR,
        cache_dir: str = DEFAULT_CACHE_DIR,
        hash_filename: str = DEFAULT_HASH_FILENAME,
    ) -> Dict[str, object]:
        hash_info = cls.get_current_layout_hash_info(cache_dir, hash_filename)
        if not hash_info.get("success"):
            return hash_info

        layout_hash = hash_info["layout_hash"]
        svg_path = os.path.join(svg_dir, f"{layout_hash}.svg")
        exists = os.path.exists(svg_path)

        hash_info.update(
            {
                "svg_path": svg_path,
                "svg_exists": exists,
            }
        )

        if not exists:
            hash_info["success"] = False
            hash_info["message"] = "SVG asset not generated yet."

        return hash_info
