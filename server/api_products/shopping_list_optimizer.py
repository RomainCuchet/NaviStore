"""
Shopping list optimization service.

Integrates product locations with path optimization for optimal shopping routes.
"""

import logging
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field

from api_products.crud import __get_products_by_ids
from api_products.path_optimization import (
    POIMapper,
    OptimizedJPS,
    TSPSolver,
    FinalPathGenerator,
    load_layout_from_h5,
    load_hash_from_json,
)

logger = logging.getLogger(__name__)


class ShoppingListItem(BaseModel):
    """Item in a shopping list with product ID and location."""

    product_id: int = Field(..., description="Product ID from the products database")
    location_x: float = Field(
        ..., description="Product location X coordinate in real-world units (cm)"
    )
    location_y: float = Field(
        ..., description="Product location Y coordinate in real-world units (cm)"
    )
    quantity: int = Field(default=1, description="Quantity needed")


class ShoppingListOptimizationRequest(BaseModel):
    """Request for shopping list optimization."""

    shopping_list: List[ShoppingListItem] = Field(
        ..., description="List of products to collect"
    )
    distance_threshold: float = Field(
        default=500.0, description="Distance threshold in cm"
    )
    max_runtime: int = Field(
        default=60, description="Maximum optimization time in seconds"
    )
    include_return_to_start: bool = Field(
        default=True, description="Return to starting position"
    )


class OptimizedShoppingRoute(BaseModel):
    """Optimized shopping route response."""

    success: bool
    total_distance: float
    total_items: int
    collection_order: List[ShoppingListItem]
    complete_path: List[Tuple[int, int]]
    products_info: List[dict]
    optimization_time: float
    route_summary: dict


class ShoppingListOptimizer:
    """
    Optimizes shopping routes by combining product data with path optimization.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _load_current_layout(self) -> Tuple[any, float, str]:
        """
        Load the current store layout.

        Returns:
            Tuple of (layout, edge_length, layout_hash)
        """
        import os

        hash_file = os.path.join("assets/cache", "current_layout.json")
        current_hash = load_hash_from_json(hash_file)

        if not current_hash:
            raise ValueError("No store layout uploaded")

        layout_file = os.path.join("assets/layouts", f"{current_hash}.h5")
        if not os.path.exists(layout_file):
            raise ValueError("Store layout file not found")

        layout, edge_length = load_layout_from_h5(layout_file)
        return layout, edge_length, current_hash

    def _get_product_details(self, product_ids: List[int]) -> List[dict]:
        """
        Get product details from the products database.

        Args:
            product_ids: List of product IDs

        Returns:
            List of product information dictionaries
        """
        try:
            products = __get_products_by_ids(product_ids)
            return products
        except Exception as e:
            self.logger.error(f"Error fetching product details: {str(e)}")
            return []

    def _validate_shopping_list(self, shopping_list: List[ShoppingListItem]) -> None:
        """
        Validate shopping list items.

        Args:
            shopping_list: List of shopping list items

        Raises:
            ValueError: If validation fails
        """
        if len(shopping_list) < 2:
            raise ValueError("Shopping list must contain at least 2 items")

        # Check for duplicate product IDs
        product_ids = [item.product_id for item in shopping_list]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Shopping list contains duplicate product IDs")

        # Validate coordinates
        for item in shopping_list:
            if item.location_x < 0 or item.location_y < 0:
                raise ValueError(
                    f"Invalid location for product {item.product_id}: "
                    f"coordinates must be non-negative"
                )

    def optimize_shopping_route(
        self, request: ShoppingListOptimizationRequest
    ) -> OptimizedShoppingRoute:
        """
        Optimize shopping route for the given shopping list.

        Args:
            request: Shopping list optimization request

        Returns:
            Optimized shopping route

        Raises:
            ValueError: If optimization fails
        """
        import time

        start_time = time.time()

        try:
            # Validate inputs
            self._validate_shopping_list(request.shopping_list)

            # Load store layout
            layout, edge_length, layout_hash = self._load_current_layout()

            # Extract POI coordinates from shopping list
            poi_coords_real = [
                (item.location_x, item.location_y) for item in request.shopping_list
            ]
            product_ids = [item.product_id for item in request.shopping_list]

            # Get product details
            products_info = self._get_product_details(product_ids)

            # Map POIs to grid
            poi_mapper = POIMapper(
                layout, request.distance_threshold, poi_coords_real, edge_length
            )
            grid_with_poi, distance_threshold_grid = poi_mapper.generate_grid()
            poi_grid_coords = poi_mapper.get_poi_grid_coordinates()

            # Load JPS cache (simplified - assumes cache exists)
            import os
            import pickle

            cache_file = os.path.join("assets/cache", f"{layout_hash}.pkl")
            jps_cache = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "rb") as f:
                        jps_cache = pickle.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load JPS cache: {str(e)}")

            # Compute optimal paths
            jps_solver = OptimizedJPS(
                grid_with_poi, jps_cache, distance_threshold_grid, poi_grid_coords
            )
            distance_matrix, path_matrix = jps_solver.compute_all_paths()

            # Solve TSP
            tsp_solver = TSPSolver(distance_matrix, max_runtime=request.max_runtime)
            visiting_order = tsp_solver.solve()

            # Generate final path
            path_generator = FinalPathGenerator(
                path_matrix, visiting_order, poi_grid_coords
            )
            complete_path = path_generator.generate_complete_path(
                request.include_return_to_start
            )

            # Reorder shopping list according to optimal visiting order
            optimized_shopping_list = [request.shopping_list[i] for i in visiting_order]

            # Calculate results
            total_distance = path_generator.calculate_total_distance()
            optimization_time = time.time() - start_time
            route_summary = path_generator.get_path_summary()

            self.logger.info(
                f"Shopping route optimized: {len(request.shopping_list)} items, "
                f"distance={total_distance:.2f}, time={optimization_time:.2f}s"
            )

            return OptimizedShoppingRoute(
                success=True,
                total_distance=total_distance,
                total_items=len(request.shopping_list),
                collection_order=optimized_shopping_list,
                complete_path=complete_path,
                products_info=products_info,
                optimization_time=optimization_time,
                route_summary=route_summary,
            )

        except Exception as e:
            self.logger.error(f"Shopping route optimization failed: {str(e)}")
            raise ValueError(f"Optimization failed: {str(e)}")

    def estimate_collection_time(
        self,
        route: OptimizedShoppingRoute,
        walking_speed_cm_per_sec: float = 100.0,
        collection_time_per_item_sec: float = 30.0,
    ) -> dict:
        """
        Estimate total collection time for the optimized route.

        Args:
            route: Optimized shopping route
            walking_speed_cm_per_sec: Walking speed in cm/second
            collection_time_per_item_sec: Time to collect each item in seconds

        Returns:
            Dictionary with time estimates
        """
        walking_time = route.total_distance / walking_speed_cm_per_sec
        collection_time = route.total_items * collection_time_per_item_sec
        total_time = walking_time + collection_time

        return {
            "walking_time_seconds": walking_time,
            "collection_time_seconds": collection_time,
            "total_time_seconds": total_time,
            "total_time_minutes": total_time / 60.0,
            "walking_distance_meters": route.total_distance / 100.0,
            "items_count": route.total_items,
        }

    def get_route_directions(self, route: OptimizedShoppingRoute) -> List[dict]:
        """
        Generate step-by-step directions for the shopping route.

        Args:
            route: Optimized shopping route

        Returns:
            List of direction steps
        """
        directions = []

        for i, item in enumerate(route.collection_order):
            # Find corresponding product info
            product_info = None
            for product in route.products_info:
                if product.get("id") == item.product_id:
                    product_info = product
                    break

            direction = {
                "step": i + 1,
                "action": "collect",
                "product_id": item.product_id,
                "product_name": (
                    product_info.get("title", "Unknown") if product_info else "Unknown"
                ),
                "location": {"x": item.location_x, "y": item.location_y},
                "quantity": item.quantity,
                "notes": f"Collect {item.quantity}x {product_info.get('title', 'item')} from location ({item.location_x:.1f}, {item.location_y:.1f})",
            }

            directions.append(direction)

        return directions
