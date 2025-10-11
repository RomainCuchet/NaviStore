"""
Router for path optimization endpoints.

Handles store layout upload, POI coordinates, and optimal path computation.
"""

from fastapi import APIRouter, Depends, UploadFile, File
import logging

from api_navimall.auth import verify_api_key, verify_write_rights
from api_navimall.path_optimization import (
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
from api_navimall.path_optimization.serialization_utils import (
    clean_optimization_response,
    clean_poi_summary,
    convert_numpy_types,
)

from api_navimall.crud import (
    _upload_store_layout,
    _optimize_shopping_path,
    _get_layout_status,
    _validate_poi_placement,
    _get_pathfinding_algorithms,
    _get_current_layout_hash,
    _get_current_layout_svg,
)
from api_navimall.models import PathOptimizationRequest, PathOptimizationResponse

router = APIRouter(prefix="/path_optimization", tags=["Path Optimization"])

logger = logging.getLogger("path_optimization")


@router.post("/upload_layout")
async def upload_store_layout(
    layout_file: UploadFile = File(
        ..., description="HDF5 file containing store layout"
    ),
    user_info: dict = Depends(verify_write_rights),
):
    return await _upload_store_layout(layout_file, user_info)


@router.post("/optimize_path", response_model=PathOptimizationResponse)
async def optimize_shopping_path(
    request: PathOptimizationRequest, user_info: dict = Depends(verify_api_key)
):

    return _optimize_shopping_path(request, user_info)


@router.get("/layout_status")
async def get_layout_status(user_info: dict = Depends(verify_api_key)):
    return _get_layout_status(user_info)


@router.post("/validate_poi_placement")
async def validate_poi_placement(
    request: PathOptimizationRequest, user_info: dict = Depends(verify_api_key)
):
    return _validate_poi_placement(request, user_info)


@router.get("/pathfinding_algorithms")
async def get_pathfinding_algorithms(user_info: dict = Depends(verify_api_key)):
    return _get_pathfinding_algorithms(user_info)


@router.get("/layout_hash")
async def get_current_layout_hash(user_info: dict = Depends(verify_api_key)):
    return _get_current_layout_hash(user_info)


@router.get("/layout_svg")
async def get_current_layout_svg(user_info: dict = Depends(verify_api_key)):
    return _get_current_layout_svg(user_info)
