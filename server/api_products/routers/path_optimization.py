"""
Router for path optimization endpoints.

Handles store layout upload, POI coordinates, and optimal path computation.
"""

import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field
import logging
import json

from api_products.auth import verify_api_key, verify_write_rights
from api_products.path_optimization import (
    StoreLayoutManager,
    POIMapper,
    PathfindingSolver,
    PathfindingSolverFactory,
    TSPSolver,
    FinalPathGenerator,
    load_layout_from_h5,
    save_hash_to_json,
    load_hash_from_json,
)
from api_products.path_optimization.serialization_utils import (
    clean_optimization_response,
    clean_poi_summary,
    convert_numpy_types,
)

router = APIRouter(prefix="/path_optimization", tags=["Path Optimization"])

# Configure logging
logger = logging.getLogger("path_optimization")

# Create directories for caching
os.makedirs("assets/cache", exist_ok=True)
os.makedirs("assets/layouts", exist_ok=True)


class POICoordinate(BaseModel):
    """Point of Interest coordinate in real-world units."""

    x: float = Field(..., description="X coordinate in real-world units (cm)")
    y: float = Field(..., description="Y coordinate in real-world units (cm)")


class PathOptimizationRequest(BaseModel):
    """Request model for path optimization."""

    poi_coordinates: List[POICoordinate] = Field(
        ..., description="List of POI coordinates"
    )
    distance_threshold: float = Field(
        default=2000.0, description="Distance threshold in real-world units (cm)"
    )
    max_runtime: int = Field(
        default=60, description="Maximum TSP solving time in seconds"
    )
    include_return_to_start: bool = Field(
        default=False, description="Include return path to starting POI"
    )
    pathfinding_algorithm: str = Field(
        default="astar",
        description="Pathfinding algorithm: 'astar', 'dijkstra', 'best_first', or 'jps'",
    )
    diagonal_movement: bool = Field(
        default=False, description="Allow diagonal movements (ignored for JPS)"
    )


class PathOptimizationResponse(BaseModel):
    """Response model for path optimization."""

    success: bool
    total_distance: float
    visiting_order: List[int]
    complete_path: List[Tuple[int, int]]
    poi_count: int
    computation_time: float
    layout_hash: str
    optimization_stats: dict
    path_summary: dict


@router.post("/upload_layout")
async def upload_store_layout(
    layout_file: UploadFile = File(
        ..., description="HDF5 file containing store layout"
    ),
    user_info: dict = Depends(verify_write_rights),
):
    """
    Upload store layout HDF5 file.

    The HDF5 file should contain:
    - 'layout': numpy array with 0=navigable, 1=POI, -1=obstacle
    - 'edge_length': size of one grid cell in centimeters
    """
    try:
        # Validate file format
        if not layout_file.filename.endswith(".h5"):
            raise HTTPException(
                status_code=422, detail="File must be in HDF5 format (.h5)"
            )

        # Save uploaded file temporarily
        temp_path = os.path.join("assets/layouts", f"temp_{layout_file.filename}")

        with open(temp_path, "wb") as buffer:
            content = await layout_file.read()
            buffer.write(content)

        # Validate the file content
        try:
            layout, edge_length = load_layout_from_h5(temp_path)

            # Move to permanent location with hash-based name
            cache_manager = StoreLayoutManager(layout)
            layout_hash = cache_manager.get_current_hash()

            permanent_path = os.path.join("assets/layouts", f"{layout_hash}.h5")
            os.rename(temp_path, permanent_path)

            # Save hash for tracking
            hash_file = os.path.join("assets/cache", "current_layout.json")
            save_hash_to_json(layout_hash, hash_file)

            logger.info(
                f"Layout uploaded successfully by user={user_info['user']}, "
                f"hash={layout_hash}, shape={layout.shape}"
            )

            return {
                "success": True,
                "layout_hash": layout_hash,
                "layout_shape": layout.shape,
                "edge_length": edge_length,
                "obstacles_count": int((layout == -1).sum()),
                "navigable_cells": int((layout >= 0).sum()),
                "filename": permanent_path,
            }

        except Exception as e:
            # Clean up temp file if validation fails
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=422, detail=f"Invalid HDF5 file: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Layout upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/optimize_path", response_model=PathOptimizationResponse)
async def optimize_shopping_path(
    request: PathOptimizationRequest, user_info: dict = Depends(verify_api_key)
):
    """
    Compute optimal shopping path for given POI coordinates.

    Requires a store layout to be uploaded first via /upload_layout.
    """
    import time

    start_time = time.time()

    try:
        # Load current layout
        hash_file = os.path.join("assets/cache", "current_layout.json")
        current_hash = load_hash_from_json(hash_file)

        if not current_hash:
            raise HTTPException(
                status_code=422,
                detail="No store layout uploaded. Please upload layout first.",
            )

        layout_file = os.path.join("assets/layouts", f"{current_hash}.h5")
        if not os.path.exists(layout_file):
            raise HTTPException(
                status_code=422,
                detail="Store layout file not found. Please re-upload layout.",
            )

        # Load layout and edge length
        layout, edge_length = load_layout_from_h5(layout_file)

        # Convert POI coordinates to list of tuples
        poi_coords_real = [(poi.x, poi.y) for poi in request.poi_coordinates]

        if len(poi_coords_real) < 2:
            raise HTTPException(
                status_code=422,
                detail="At least 2 POIs are required for path optimization",
            )

        # Step 1: Layout versioning management
        layout_manager = StoreLayoutManager(
            layout, current_hash, svg_assets_dir="assets/svg"
        )

        # Step 2: POI mapping
        poi_mapper = POIMapper(
            layout, request.distance_threshold, poi_coords_real, edge_length
        )
        grid_with_poi, distance_threshold_grid = poi_mapper.generate_grid()
        poi_grid_coords = poi_mapper.get_poi_grid_coordinates()

        # Step 3: Update svg assets if needed
        layout_hash, svg_path = layout_manager.update_svg_if_needed()
        generated_layout_svg = layout_hash == current_hash

        try:
            solver = PathfindingSolverFactory.create_solver(
                grid_with_poi=grid_with_poi,
                distance_threshold_grid=distance_threshold_grid,
                poi_coords=poi_grid_coords,
                algorithm=request.pathfinding_algorithm,
                diagonal_movement=request.diagonal_movement,
            )
            logger.info(
                f"Using {request.pathfinding_algorithm.upper()} pathfinding algorithm"
            )
        except ImportError:
            # Fallback to JPS if pathfinding library not available
            logger.warning("pathfinding library not available")

        except ValueError as e:
            # Invalid algorithm, fallback to A*
            logger.warning(
                f"Invalid algorithm {request.pathfinding_algorithm}, falling back to A*"
            )
            solver = PathfindingSolverFactory.create_solver(
                grid_with_poi=grid_with_poi,
                distance_threshold_grid=distance_threshold_grid,
                poi_coords=poi_grid_coords,
                algorithm="astar",
                diagonal_movement=request.diagonal_movement,
            )

        distance_matrix, path_matrix = solver.compute_all_paths()

        # Step 5: TSP solving
        tsp_solver = TSPSolver(distance_matrix, max_runtime=request.max_runtime)
        visiting_order = tsp_solver.solve()

        # Step 6: Final path generation with A* fallback support
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

        # Calculate results
        total_distance = path_generator.calculate_total_distance()
        computation_time = time.time() - start_time

        # Get statistics
        optimization_stats = solver.get_optimization_stats()
        path_summary = path_generator.get_path_summary()

        logger.info(
            f"Path optimization completed for user={user_info['user']}, "
            f"POIs={len(poi_coords_real)}, distance={total_distance:.2f}, "
            f"time={computation_time:.2f}s"
        )

        # Create response with cleaned data (no NumPy types)
        response_data = {
            "success": True,
            "total_distance": float(total_distance),
            "visiting_order": visiting_order,
            "complete_path": complete_path,
            "poi_count": len(poi_coords_real),
            "computation_time": float(computation_time),
            "generated_layout_svg": generated_layout_svg,
            "layout_hash": layout_hash,
            "optimization_stats": optimization_stats,
            "path_summary": path_summary,
        }

        # Clean all NumPy types from response
        cleaned_response = clean_optimization_response(response_data)

        return PathOptimizationResponse(**cleaned_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Path optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/layout_status")
async def get_layout_status(user_info: dict = Depends(verify_api_key)):
    """
    Get current store layout status and information.
    """
    try:
        hash_file = os.path.join("assets/cache", "current_layout.json")
        current_hash = load_hash_from_json(hash_file)

        if not current_hash:
            return {"layout_uploaded": False, "message": "No store layout uploaded"}

        layout_file = os.path.join("assets/layouts", f"{current_hash}.h5")
        if not os.path.exists(layout_file):
            return {
                "layout_uploaded": False,
                "message": "Store layout file not found",
                "hash": current_hash,
            }

        # Load layout info
        layout, edge_length = load_layout_from_h5(layout_file)

        return {
            "layout_uploaded": True,
            "layout_hash": current_hash,
            "layout_shape": layout.shape,
            "edge_length": edge_length,
            "obstacles_count": int((layout == -1).sum()),
            "navigable_cells": int((layout >= 0).sum()),
            "cache_available": os.path.exists(
                os.path.join("assets/cache", f"{current_hash}.pkl")
            ),
        }

    except Exception as e:
        logger.error(f"Layout status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/validate_poi_placement")
async def validate_poi_placement(
    request: PathOptimizationRequest, user_info: dict = Depends(verify_api_key)
):
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
        layout, edge_length = load_layout_from_h5(layout_file)

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


@router.get("/pathfinding_algorithms")
async def get_pathfinding_algorithms(user_info: dict = Depends(verify_api_key)):
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
