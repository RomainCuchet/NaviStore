"""
Utility functions for JPS-TSP path optimization.
"""

import h5py
import numpy as np
import json
import os
import xxhash
from typing import Tuple, Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Zone:
    """Represents a polygon zone in the store layout."""

    def __init__(self, name: str, points: List[Tuple[float, float]]):
        self.name = name
        self.points = points  # List of (x, y) coordinates forming polygon

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "points": self.points}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Zone":
        return cls(data["name"], data["points"])


def load_layout_from_h5(h5_filename: str) -> Tuple[np.ndarray, float, Dict[str, Zone]]:
    """
    Load store layout, edge length, and zones from HDF5 file.

    Args:
        h5_filename: Path to the .h5 file

    Returns:
        Tuple of (layout_array, edge_length_cm, zones_dict)

    Cell types in layout_array:
        0 = navigable cell
        1 = point of interest (POI)
        -1 = obstacle (non-navigable)
        2 = shelf (non-navigable)

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

            # Validate cell types
            valid_cells = {0, 1, -1, 2}  # navigable, POI, obstacle, shelf
            unique_cells = set(np.unique(layout))
            invalid_cells = unique_cells - valid_cells
            if invalid_cells:
                raise ValueError(
                    f"Invalid cell types found: {invalid_cells}. Valid types: {valid_cells}"
                )

            # Load edge length parameter
            if "edge_length" not in f:
                raise ValueError("Missing 'edge_length' dataset in HDF5 file")
            edge_length = float(f["edge_length"][()])

            # Load zones (optional)
            zones = {}
            if "zones" in f:
                zones_group = f["zones"]
                for zone_id in zones_group.keys():
                    zone_group = zones_group[zone_id]
                    if "name" in zone_group and "points" in zone_group:
                        name = (
                            zone_group["name"][()].decode("utf-8")
                            if isinstance(zone_group["name"][()], bytes)
                            else str(zone_group["name"][()])
                        )
                        points = zone_group["points"][:].tolist()
                        zones[zone_id] = Zone(name, points)
                    else:
                        logger.warning(
                            f"Zone {zone_id} missing required data, skipping"
                        )

            logger.info(
                f"Loaded layout with shape {layout.shape}, edge_length={edge_length}cm, "
                f"zones={len(zones)}, cell_types={sorted(unique_cells)}"
            )
            return layout, edge_length, zones

    except Exception as e:
        raise ValueError(f"Error reading HDF5 file {h5_filename}: {str(e)}")


def calculate_layout_hash(grid: np.ndarray, edge_length: float) -> str:
    """
    Calculate a unique hash for a grid layout.

    Args:
        grid: 2D numpy array representing the grid
        edge_length: Edge length of grid cells

    Returns:
        Hexadecimal string representation of the hash
    """
    # Convert grid to bytes and hash it along with edge_length
    grid_bytes = grid.astype(np.uint8).tobytes()
    edge_bytes = str(edge_length).encode("utf-8")
    combined_data = grid_bytes + edge_bytes

    return xxhash.xxh3_64(combined_data).hexdigest()


def save_layout_to_h5(
    h5_filename: str,
    layout: np.ndarray,
    edge_length: float,
    zones: Dict[str, Zone] = None,
    layout_hash: str = None,
) -> None:
    """
    Save store layout, edge length, and zones to HDF5 file.

    Args:
        h5_filename: Path to the .h5 file
        layout: Layout array with cell types (0=navigable, 1=POI, -1=obstacle, 2=shelf)
        edge_length: Size of one grid cell in centimeters
        zones: Dictionary of zones {zone_id: Zone}
        layout_hash: Optional hash for integrity verification
    """
    try:
        with h5py.File(h5_filename, "w") as f:
            # Save layout array
            f.create_dataset("layout", data=layout, compression="gzip")

            # Save edge length
            f.create_dataset("edge_length", data=edge_length)

            # Save layout hash if provided
            if layout_hash:
                f.create_dataset("layout_hash", data=layout_hash.encode("utf-8"))

            # Save zones if provided
            if zones:
                zones_group = f.create_group("zones")
                for zone_id, zone in zones.items():
                    zone_group = zones_group.create_group(zone_id)
                    zone_group.create_dataset("name", data=zone.name.encode("utf-8"))
                    zone_group.create_dataset("points", data=np.array(zone.points))

            logger.info(
                f"Saved layout to {h5_filename} with {len(zones) if zones else 0} zones"
            )

    except Exception as e:
        raise ValueError(f"Error saving HDF5 file {h5_filename}: {str(e)}")


def save_grid_with_metadata(
    grid: np.ndarray,
    edge_length: float,
    zones: Dict[str, Zone] = None,
    output_dir: str = "server/assets",
    filename_prefix: str = "map_layout",
    include_timestamp: bool = True,
) -> Tuple[str, str]:
    """
    Save grid with metadata using the same process as the grid editor.

    Args:
        grid: 2D numpy array representing the grid
        edge_length: Edge length of grid cells in cm
        zones: Dictionary of zone objects (optional)
        output_dir: Directory to save the file
        filename_prefix: Prefix for the filename
        include_timestamp: Whether to include timestamp in filename

    Returns:
        Tuple of (filepath, layout_hash)
    """
    import datetime

    # Calculate layout hash
    layout_hash = calculate_layout_hash(grid, edge_length)

    # Generate filename
    if include_timestamp:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.h5"
    else:
        filename = f"{filename_prefix}.h5"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # Save the layout
    save_layout_to_h5(
        h5_filename=filepath,
        layout=grid,
        edge_length=edge_length,
        zones=zones or {},
        layout_hash=layout_hash,
    )

    # Add hash as attribute for compatibility with grid editor
    with h5py.File(filepath, "a") as f:
        f.attrs["layout_hash"] = layout_hash
        f.attrs["created_with"] = "NaviStore Automatic Grid Generator"

    # Log save information
    logger.info(f"Grid saved to: {filepath}")
    logger.info(f"Grid shape: {grid.shape}")
    logger.info(f"Edge length: {edge_length} cm")
    logger.info(f"Layout hash: {layout_hash}")
    if zones:
        logger.info(f"Zones saved: {len(zones)}")

    return filepath, layout_hash


def get_cell_type_info() -> Dict[int, Dict[str, Any]]:
    """
    Get information about supported cell types.

    Returns:
        Dictionary mapping cell values to their properties
    """
    return {
        0: {
            "name": "navigable",
            "walkable": True,
            "color": "white",
            "description": "Free zone",
        },
        1: {
            "name": "poi",
            "walkable": True,
            "color": "green",
            "description": "Point of Interest",
        },
        -1: {
            "name": "obstacle",
            "walkable": False,
            "color": "black",
            "description": "Obstacle",
        },
        2: {
            "name": "shelf",
            "walkable": False,
            "color": "brown",
            "description": "Shelf (non-navigable)",
        },
    }


def is_valid_cell_type(cell_value: int) -> bool:
    """
    Check if a cell value is a valid cell type.

    Args:
        cell_value: Cell value from the layout array

    Returns:
        True if cell type is valid, False otherwise
    """
    valid_types = get_cell_type_info().keys()
    return cell_value in valid_types


def is_cell_navigable(cell_value: int) -> bool:
    """
    Check if a cell value represents a navigable cell.

    Args:
        cell_value: Cell value from the layout array

    Returns:
        True if cell is navigable, False otherwise
    """
    # Only 0 (navigable) and 1 (POI) are walkable
    # -1 (obstacle) and 2 (shelf) are non-navigable
    return cell_value >= 0


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
