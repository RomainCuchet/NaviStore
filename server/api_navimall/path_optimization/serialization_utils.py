"""
Utilities for handling NumPy types in API responses.

Converts NumPy types to native Python types for proper JSON serialization.
"""

import numpy as np
from typing import Any, Dict, List, Tuple, Union


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types.

    Args:
        obj: Object that may contain NumPy types

    Returns:
        Object with NumPy types converted to Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        converted = [convert_numpy_types(item) for item in obj]
        return converted if isinstance(obj, list) else tuple(converted)
    else:
        return obj


def clean_path_coordinates(path: List[Tuple[Any, Any]]) -> List[Tuple[int, int]]:
    """
    Clean path coordinates to ensure they are native Python ints.

    Args:
        path: List of coordinate tuples that may contain NumPy types

    Returns:
        List of coordinate tuples with native Python ints
    """
    return [(int(x), int(y)) for x, y in path]


def clean_optimization_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean an entire optimization response to remove NumPy types.

    Args:
        response_data: Response dictionary that may contain NumPy types

    Returns:
        Cleaned response dictionary with native Python types
    """
    cleaned = convert_numpy_types(response_data)

    # Specifically clean path coordinates if present
    if "complete_path" in cleaned:
        cleaned["complete_path"] = clean_path_coordinates(cleaned["complete_path"])

    # Clean visiting order
    if "visiting_order" in cleaned:
        cleaned["visiting_order"] = [int(x) for x in cleaned["visiting_order"]]

    return cleaned


def clean_poi_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean POI summary data to remove NumPy types.

    Args:
        summary: POI summary dictionary

    Returns:
        Cleaned summary with native Python types
    """
    cleaned = convert_numpy_types(summary)

    # Specifically handle grid coordinates
    if "grid_coords" in cleaned and cleaned["grid_coords"] is not None:
        cleaned["grid_coords"] = [
            [int(coord) for coord in point] for point in cleaned["grid_coords"]
        ]

    return cleaned
