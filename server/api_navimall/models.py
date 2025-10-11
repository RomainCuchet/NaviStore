from typing import List, Tuple

from pydantic import BaseModel, Field


class POICoordinate(BaseModel):
    """Point of Interest coordinate in real-world units."""

    x: float = Field(..., description="X coordinate in centimeters")
    y: float = Field(..., description="Y coordinate in centimeters")


class PathOptimizationRequest(BaseModel):
    """Payload model for path optimization requests."""

    poi_coordinates: List[POICoordinate] = Field(
        ..., description="List of POI coordinates expressed in centimeters"
    )
    distance_threshold: float = Field(
        default=2000.0, description="Distance threshold in centimeters"
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
    """Response model for path optimization results."""

    success: bool
    total_distance: float
    visiting_order: List[int]
    complete_path: List[Tuple[int, int]]
    poi_count: int
    computation_time: float
    layout_hash: str
    optimization_stats: dict
    path_summary: dict
    generated_layout_svg: bool | None = Field(
        default=None,
        description="Whether the layout SVG was generated during this optimization run",
    )


__all__ = [
    "POICoordinate",
    "PathOptimizationRequest",
    "PathOptimizationResponse",
]
