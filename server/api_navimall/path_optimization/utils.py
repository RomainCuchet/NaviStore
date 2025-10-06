"""
Utility functions for JPS-TSP path optimization.
"""

import h5py
import numpy as np
import json
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def load_layout_from_h5(h5_filename: str) -> Tuple[np.ndarray, float]:
    """
    Load store layout and edge length from HDF5 file.

    Args:
        h5_filename: Path to the .h5 file

    Returns:
        Tuple of (layout_array, edge_length_cm)

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is invalid
    """
    if not os.path.exists(h5_filename):
        raise FileNotFoundError(f"HDF5 file not found: {h5_filename}")

    try:
        with h5py.File(h5_filename, "r") as f:
            # Load the grid layout
            if "layout" not in f:
                raise ValueError("Missing 'layout' dataset in HDF5 file")
            layout = np.array(f["layout"])

            # Load edge length parameter
            if "edge_length" not in f:
                raise ValueError("Missing 'edge_length' dataset in HDF5 file")
            edge_length = float(f["edge_length"][()])

            logger.info(
                f"Loaded layout with shape {layout.shape}, edge_length={edge_length}cm"
            )
            return layout, edge_length

    except Exception as e:
        raise ValueError(f"Error reading HDF5 file {h5_filename}: {str(e)}")


def save_hash_to_json(hash_value: str, json_filename: str) -> None:
    """
    Save layout hash to JSON file.

    Args:
        hash_value: The XXH3 hash string
        json_filename: Path to the JSON file
    """
    data = {"layout_hash": hash_value}
    os.makedirs(os.path.dirname(json_filename), exist_ok=True)

    with open(json_filename, "w") as f:
        json.dump(data, f)

    logger.debug(f"Saved hash {hash_value} to {json_filename}")


def load_hash_from_json(json_filename: str) -> Optional[str]:
    """
    Load layout hash from JSON file.

    Args:
        json_filename: Path to the JSON file

    Returns:
        The hash string or None if file doesn't exist or is invalid
    """
    if not os.path.exists(json_filename):
        logger.debug(f"Hash file {json_filename} not found")
        return None

    try:
        with open(json_filename, "r") as f:
            data = json.load(f)

        hash_value = data.get("layout_hash")
        logger.debug(f"Loaded hash {hash_value} from {json_filename}")
        return hash_value

    except Exception as e:
        logger.warning(f"Error reading hash file {json_filename}: {str(e)}")
        return None


def real_world_to_grid_coords(
    real_coords: np.ndarray, edge_length: float
) -> np.ndarray:
    """
    Convert real-world coordinates to grid indices.
    Note: Real-world (x, y) maps to grid (x=row, y=col) with origin at top-left
    Assumes real-world coordinates represent cell centers.

    Args:
        real_coords: Array of shape (N, 2) with real-world coordinates (x, y)
        edge_length: Size of one grid cell in centimeters

    Returns:
        Array of shape (N, 2) with grid indices (x=row, y=col)
    """
    # Convert to grid coordinates - x becomes row, y becomes col
    # Real-world coords are cell centers, so direct division and floor gives correct index
    grid_coords = np.floor(real_coords / edge_length).astype(int)
    return grid_coords  # Already in (x=row, y=col) format


def grid_to_real_world_coords(
    grid_coords: np.ndarray, edge_length: float
) -> np.ndarray:
    """
    Convert grid indices to real-world coordinates.
    Note: Grid (x=row, y=col) maps to real-world (x, y) with origin at top-left
    Returns coordinates of cell centers.

    Args:
        grid_coords: Array of shape (N, 2) with grid indices (x=row, y=col)
        edge_length: Size of one grid cell in centimeters

    Returns:
        Array of shape (N, 2) with real-world coordinates (x, y) at cell centers
    """
    # Convert to cell centers by adding 0.5 to grid indices
    real_coords = (grid_coords + 0.5) * edge_length
    return real_coords  # x=(row+0.5)*edge_length, y=(col+0.5)*edge_length


def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    """
    Calculate Manhattan distance between two grid points.

    Args:
        p1: First point (x, y)
        p2: Second point (x, y)

    Returns:
        Manhattan distance
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def euclidean_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    """
    Calculate Euclidean distance between two grid points.

    Args:
        p1: First point (x, y)
        p2: Second point (x, y)

    Returns:
        Euclidean distance
    """
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
