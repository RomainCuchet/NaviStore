# crud stands for Create, Read, Update, Delete
import logging
import os
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from api_navimall.models import PathOptimizationRequest, PathOptimizationResponse
from api_navimall.path_optimization import (
    StoreLayoutManager,
    POIMapper,
    PathfindingSolverFactory,
    TSPSolver,
    FinalPathGenerator,
    load_layout_from_h5,
    save_hash_to_json,
    load_hash_from_json,
)
from api_navimall.path_optimization.serialization_utils import (
    clean_optimization_response,
    clean_poi_summary,
)
from api_navimall.path_optimization.utils import grid_to_real_world_coords


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _upload_store_layout(layout_file: UploadFile, user_info: dict):
    """Upload store layout HDF5 file using StoreLayoutManager logic."""
    result = await StoreLayoutManager.upload_layout(layout_file, user_info)
    logger.info(
        "Layout upload processed for user=%s, hash=%s, updated=%s",
        user_info.get("user"),
        result.get("layout_hash"),
        result.get("updated"),
    )
    return result


def _get_current_layout_hash(user_info: dict):
    """Return information about the current layout hash."""
    return StoreLayoutManager.get_current_layout_hash_info()


def _get_current_layout_svg_infos(user_info: dict):
    """Return information about the current layout SVG asset."""
    return StoreLayoutManager.get_current_svg_info()


def _get_current_layout_svg_file(user_info: dict):
    """Return the current layout SVG file as a streamed response."""
    info = StoreLayoutManager.get_current_svg_info()
    if not info.get("success"):
        raise HTTPException(
            status_code=404, detail=info.get("message", "SVG not available")
        )

    svg_path = info.get("svg_path")
    if not svg_path or not os.path.exists(svg_path):
        raise HTTPException(status_code=404, detail="SVG file not found")

    return FileResponse(svg_path, media_type="image/svg+xml")


def _get_layout_status(user_info: dict):
    """
    Get current store layout status and information.
    """
    try:
        hash_file = os.path.join("assets/cache", "current_layout.json")
        current_layout_hash = load_hash_from_json(hash_file)

        if not current_layout_hash:
            return {"layout_uploaded": False, "message": "No store layout uploaded"}

        layout_file = os.path.join("assets/layouts", f"{current_layout_hash}.h5")
        if not os.path.exists(layout_file):
            return {
                "layout_uploaded": False,
                "message": "Store layout file not found",
                "hash": current_layout_hash,
            }

        # Load layout info
        layout, edge_length, _ = load_layout_from_h5(layout_file)

        return {
            "layout_uploaded": True,
            "layout_hash": current_layout_hash,
            "layout_shape": layout.shape,
            "edge_length": edge_length,
            "obstacles_count": int((layout == -1).sum()),
            "navigable_cells": int((layout >= 0).sum()),
            "cache_available": os.path.exists(
                os.path.join("assets/cache", f"{current_layout_hash}.pkl")
            ),
        }

    except Exception as e:
        logger.error(f"Layout status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


def _optimize_shopping_path(request: PathOptimizationRequest, user_info: dict):
    """Compute optimal shopping path for given POI coordinates."""
    import time

    start_time = time.time()

    # Load hash of current layout
    hash_file = os.path.join("assets/cache", "current_layout.json")
    current_hash = load_hash_from_json(hash_file)

    if not current_hash:
        raise HTTPException(
            status_code=422,
            detail="No store layout uploaded. Please upload layout first.",
        )

    layout_path = os.path.join("assets/layouts", f"{current_hash}.h5")
    if not os.path.exists(layout_path):
        raise HTTPException(
            status_code=422,
            detail="Store layout file not found. Please re-upload layout.",
        )

    try:
        layout, edge_length, _ = load_layout_from_h5(layout_path)
    except Exception as exc:
        logger.error("Failed to load layout: %s", exc)
        raise HTTPException(status_code=500, detail="Invalid store layout file")

    poi_coords_real = [(poi.x, poi.y) for poi in request.poi_coordinates]
    if len(poi_coords_real) < 2:
        raise HTTPException(
            status_code=422,
            detail="At least 2 POIs are required for path optimization",
        )

    layout_manager = StoreLayoutManager(
        layout=layout,
        previous_hash=current_hash,
        svg_assets_dir="assets/svg",
        layout_path=layout_path,
        edge_length=edge_length,
    )

    poi_mapper = POIMapper(
        layout, request.distance_threshold, poi_coords_real, edge_length
    )
    grid_with_poi, distance_threshold_grid = poi_mapper.generate_grid()
    poi_grid_coords = poi_mapper.get_poi_grid_coordinates()

    layout_hash, _ = layout_manager.update_svg_if_needed(layout_path)
    generated_layout_svg = layout_manager.last_svg_updated

    try:
        solver = PathfindingSolverFactory.create_solver(
            grid_with_poi=grid_with_poi,
            distance_threshold_grid=distance_threshold_grid,
            poi_coords=poi_grid_coords,
            algorithm=request.pathfinding_algorithm,
            diagonal_movement=request.diagonal_movement,
        )
        logger.info(
            "Using %s pathfinding algorithm",
            request.pathfinding_algorithm.upper(),
        )
    except ImportError:
        logger.warning("pathfinding library not available, falling back to A*")
        solver = PathfindingSolverFactory.create_solver(
            grid_with_poi=grid_with_poi,
            distance_threshold_grid=distance_threshold_grid,
            poi_coords=poi_grid_coords,
            algorithm="astar",
            diagonal_movement=request.diagonal_movement,
        )
    except ValueError as exc:
        logger.warning("%s. Falling back to A*", exc)
        solver = PathfindingSolverFactory.create_solver(
            grid_with_poi=grid_with_poi,
            distance_threshold_grid=distance_threshold_grid,
            poi_coords=poi_grid_coords,
            algorithm="astar",
            diagonal_movement=request.diagonal_movement,
        )

    distance_matrix, path_matrix = solver.compute_all_paths()

    tsp_solver = TSPSolver(distance_matrix, max_runtime=request.max_runtime)
    visiting_order = tsp_solver.solve()

    path_generator = FinalPathGenerator(
        path_matrix=path_matrix,
        visiting_order=visiting_order,
        poi_coords=poi_grid_coords,
        grid_with_poi=grid_with_poi,
        pathfinding_algorithm=request.pathfinding_algorithm,
        diagonal_movement=request.diagonal_movement,
    )
    complete_path = path_generator.generate_complete_path(
        request.include_return_to_start
    )

    # Convert grid path to real-world coordinates using centralized utils
    try:
        import numpy as np

        # complete_path is a list of (row, col); convert in batch for consistency
        complete_path_array = np.array(complete_path, dtype=float).reshape(-1, 2)
        complete_path_real_array = grid_to_real_world_coords(
            complete_path_array, edge_length
        )
        complete_path_real = complete_path_real_array.tolist()
    except Exception as conv_exc:
        logger.warning(
            "Failed batch grid->real conversion, falling back to passthrough: %s",
            conv_exc,
        )
        # Fallback to original points if conversion fails
        complete_path_real = [list(pt) for pt in complete_path]

    total_distance = path_generator.calculate_total_distance()
    computation_time = time.time() - start_time

    optimization_stats = solver.get_optimization_stats()
    path_summary = path_generator.get_path_summary()

    logger.info(
        "Path optimization completed for user=%s, POIs=%d, distance=%.2f, time=%.2fs",
        user_info["user"],
        len(poi_coords_real),
        total_distance,
        computation_time,
    )

    response_data = {
        "success": True,
        "total_distance": float(total_distance),
        "visiting_order": visiting_order,
        "complete_path": complete_path_real,
        "poi_count": len(poi_coords_real),
        "computation_time": float(computation_time),
        "generated_layout_svg": generated_layout_svg,
        "layout_hash": layout_hash,
        "optimization_stats": optimization_stats,
        "path_summary": path_summary,
    }

    cleaned_response = clean_optimization_response(response_data)
    return PathOptimizationResponse(**cleaned_response)


def _validate_poi_placement(request: PathOptimizationRequest, user_info: dict):
    """
    Validate POI placement without computing full optimization.

    Useful for checking if POI coordinates are valid before optimization.
    """
    try:
        # Load current layout
        hash_file = os.path.join("assets/cache", "current_layout.json")
        current_hash = load_hash_from_json(hash_file)

        if not current_hash:
            raise HTTPException(status_code=422, detail="No store layout uploaded")

        layout_file = os.path.join("assets/layouts", f"{current_hash}.h5")
        layout, edge_length, _ = load_layout_from_h5(layout_file)

        # Convert POI coordinates
        poi_coords_real = [(poi.x, poi.y) for poi in request.poi_coordinates]

        # Validate POI placement
        poi_mapper = POIMapper(
            layout, request.distance_threshold, poi_coords_real, edge_length
        )
        poi_summary = poi_mapper.get_poi_summary()

        logger.info(
            f"POI validation for user={user_info['user']}, "
            f"POIs={len(poi_coords_real)}, valid={poi_summary['valid_placement']}"
        )

        # Clean NumPy types from POI summary
        cleaned_summary = clean_poi_summary(poi_summary)

        return {"success": True, "poi_summary": cleaned_summary}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POI validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


def _get_pathfinding_algorithms(user_info: dict):
    """
    Get list of available pathfinding algorithms and their recommendations.
    """
    try:
        algorithms = PathfindingSolverFactory.get_available_algorithms()

        return {
            "success": True,
            "algorithms": algorithms,
            "descriptions": {
                "astar": "A* Algorithm - Balanced performance and optimality, good general purpose",
                "dijkstra": "Dijkstra's Algorithm - Guaranteed shortest path, slower but very reliable",
                "best_first": "Best First Search - Faster for large grids, may not find optimal path",
            },
            "recommendations": {
                "small_grid_few_pois": "astar",
                "large_grid_many_pois": "best_first",
                "maximum_reliability": "dijkstra",
                "diagonal_optimization": "jps",
            },
            "default": "astar",
        }
    except Exception as e:
        logger.error(f"Error getting pathfinding algorithms: {str(e)}")
        return {
            "success": False,
            "algorithms": ["jps"],  # Fallback to JPS only
            "error": str(e),
        }
