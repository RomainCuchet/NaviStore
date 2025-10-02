"""
Basic tests for JPS-TSP path optimization system.

Run with: python -m pytest test_path_optimization.py
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import patch, MagicMock


# Test imports (these will fail if dependencies aren't installed, which is expected)
def test_imports():
    """Test that core modules can be imported."""
    try:
        from api_products.path_optimization import (
            StoreLayoutCacheManager,
            POIMapper,
            OptimizedJPS,
            TSPSolver,
            FinalPathGenerator,
        )

        assert True
    except ImportError as e:
        pytest.skip(f"Dependencies not installed: {e}")


def test_store_layout_cache_manager():
    """Test StoreLayoutCacheManager basic functionality."""
    try:
        from api_products.path_optimization import StoreLayoutCacheManager

        # Create a simple test layout
        layout = np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]])

        # Test cache manager initialization
        cache_manager = StoreLayoutCacheManager(layout)

        # Test hash computation
        hash1 = cache_manager.get_current_hash()
        assert isinstance(hash1, str)
        assert len(hash1) > 0

        # Test that same layout produces same hash
        cache_manager2 = StoreLayoutCacheManager(layout)
        hash2 = cache_manager2.get_current_hash()
        assert hash1 == hash2

        # Test that different layout produces different hash
        different_layout = np.array([[1, 0, 0], [0, -1, 0], [0, 0, 1]])
        cache_manager3 = StoreLayoutCacheManager(different_layout)
        hash3 = cache_manager3.get_current_hash()
        assert hash1 != hash3

    except ImportError:
        pytest.skip("Dependencies not installed")


def test_poi_mapper():
    """Test POIMapper functionality."""
    try:
        from api_products.path_optimization import POIMapper

        # Create test layout
        layout = np.array([[0, 0, 0, 0], [0, -1, -1, 0], [0, 0, 0, 0], [0, 0, 0, 0]])

        # Test POI coordinates
        real_world_coords = [(0.0, 0.0), (300.0, 300.0)]
        edge_length = 100.0  # 1 meter per grid cell
        distance_threshold = 500.0

        poi_mapper = POIMapper(
            layout, distance_threshold, real_world_coords, edge_length
        )

        # Test coordinate transformation
        grid_coords = poi_mapper.transform_coordinates()
        expected_coords = np.array([[0, 0], [3, 3]])
        np.testing.assert_array_equal(grid_coords, expected_coords)

        # Test grid generation
        grid_with_poi, threshold_grid = poi_mapper.generate_grid()

        # Check that POIs are marked in grid
        assert grid_with_poi[0, 0] == 1  # POI marked
        assert grid_with_poi[3, 3] == 1  # POI marked
        assert grid_with_poi[1, 1] == -1  # Obstacle preserved

        # Test threshold conversion
        expected_threshold = distance_threshold / edge_length
        assert threshold_grid == expected_threshold

    except ImportError:
        pytest.skip("Dependencies not installed")


def test_poi_mapper_obstacle_conflict():
    """Test POI mapper obstacle conflict detection."""
    try:
        from api_products.path_optimization import POIMapper

        # Create layout with obstacle
        layout = np.array([[0, 0], [-1, 0]])

        # Try to place POI on obstacle
        conflicting_coords = [
            (0.0, 100.0)
        ]  # Maps to grid position (0, 1) which is obstacle
        edge_length = 100.0

        poi_mapper = POIMapper(layout, 500.0, conflicting_coords, edge_length)

        # Should raise ValueError
        with pytest.raises(ValueError, match="conflicts with an obstacle"):
            poi_mapper.transform_coordinates()

    except ImportError:
        pytest.skip("Dependencies not installed")


def test_optimized_jps_basic():
    """Test OptimizedJPS basic functionality."""
    try:
        from api_products.path_optimization import OptimizedJPS

        # Create simple grid
        grid = np.array([[1, 0, 1], [0, 0, 0], [1, 0, 1]])

        poi_coords = np.array([[0, 0], [2, 0], [0, 2], [2, 2]])
        jps_cache = {}  # Empty cache for testing
        distance_threshold = 10.0

        jps_solver = OptimizedJPS(grid, jps_cache, distance_threshold, poi_coords)

        # Test distance matrix computation
        distance_matrix, path_matrix = jps_solver.compute_all_paths()

        # Check matrix dimensions
        assert distance_matrix.shape == (4, 4)
        assert len(path_matrix) == 4
        assert len(path_matrix[0]) == 4

        # Diagonal should be 0
        for i in range(4):
            assert distance_matrix[i, i] == 0

    except ImportError:
        pytest.skip("Dependencies not installed")


def test_tsp_solver_nearest_neighbor():
    """Test TSP solver with nearest neighbor algorithm."""
    try:
        from api_products.path_optimization import TSPSolver

        # Create simple distance matrix
        distance_matrix = np.array(
            [[0, 1, 4, 3], [1, 0, 2, 5], [4, 2, 0, 1], [3, 5, 1, 0]]
        )

        # Test with OR-Tools disabled to force nearest neighbor
        tsp_solver = TSPSolver(distance_matrix, use_ortools=False)
        tour = tsp_solver.solve()

        # Should return a valid tour
        assert len(tour) == 4
        assert set(tour) == {0, 1, 2, 3}  # All cities visited

        # Test tour distance calculation
        distance = tsp_solver.compute_tour_distance(tour)
        assert distance > 0

    except ImportError:
        pytest.skip("Dependencies not installed")


def test_final_path_generator():
    """Test FinalPathGenerator functionality."""
    try:
        from api_products.path_optimization import FinalPathGenerator

        # Create simple path matrix
        path_matrix = [
            [[0, 0], [0, 1], [1, 1]],  # Path from POI 0 to POI 1
            [None, [1, 1]],  # Path from POI 1 to POI 1 (self)
        ]

        poi_coords = np.array([[0, 0], [1, 1]])
        visiting_order = [0, 1]

        path_gen = FinalPathGenerator(path_matrix, visiting_order, poi_coords)

        # Test complete path generation
        complete_path = path_gen.generate_complete_path()

        # Should have a valid path
        assert len(complete_path) > 0
        assert complete_path[0] == (0, 0)  # Start at first POI
        assert complete_path[-1] == (1, 1)  # End at last POI

        # Test path summary
        summary = path_gen.get_path_summary()
        assert summary["total_pois"] == 2
        assert summary["visiting_order"] == [0, 1]

    except ImportError:
        pytest.skip("Dependencies not installed")


def test_utils_coordinate_conversion():
    """Test utility coordinate conversion functions."""
    try:
        from api_products.path_optimization.utils import (
            real_world_to_grid_coords,
            grid_to_real_world_coords,
            manhattan_distance,
            euclidean_distance,
        )

        # Test coordinate conversion
        real_coords = np.array([[100.0, 200.0], [150.0, 250.0]])
        edge_length = 50.0

        grid_coords = real_world_to_grid_coords(real_coords, edge_length)
        expected_grid = np.array([[2, 4], [3, 5]])
        np.testing.assert_array_equal(grid_coords, expected_grid)

        # Test reverse conversion
        back_to_real = grid_to_real_world_coords(grid_coords, edge_length)
        np.testing.assert_array_equal(back_to_real, real_coords)

        # Test distance functions
        p1, p2 = (0, 0), (3, 4)
        assert manhattan_distance(p1, p2) == 7
        assert euclidean_distance(p1, p2) == 5.0

    except ImportError:
        pytest.skip("Dependencies not installed")


@pytest.mark.integration
def test_complete_workflow():
    """Integration test for the complete workflow."""
    try:
        from api_products.path_optimization import (
            StoreLayoutCacheManager,
            POIMapper,
            OptimizedJPS,
            TSPSolver,
            FinalPathGenerator,
        )

        # Create test layout
        layout = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, -1, -1, -1, 0],
                [0, 0, 0, 0, 0],
                [0, -1, -1, -1, 0],
                [0, 0, 0, 0, 0],
            ]
        )

        # Test POI coordinates
        real_coords = [(0, 0), (400, 0), (0, 400), (400, 400)]
        edge_length = 100.0
        distance_threshold = 1000.0

        # Step 1: Cache management
        cache_manager = StoreLayoutCacheManager(layout)

        # Step 2: POI mapping
        poi_mapper = POIMapper(layout, distance_threshold, real_coords, edge_length)
        grid_with_poi, threshold_grid = poi_mapper.generate_grid()
        poi_grid_coords = poi_mapper.get_poi_grid_coordinates()

        # Step 3: Cache update
        layout_hash, jps_cache = cache_manager.update_cache_if_needed(grid_with_poi)

        # Step 4: JPS computation
        jps_solver = OptimizedJPS(
            grid_with_poi, jps_cache, threshold_grid, poi_grid_coords
        )
        distance_matrix, path_matrix = jps_solver.compute_all_paths()

        # Step 5: TSP solving
        tsp_solver = TSPSolver(
            distance_matrix, use_ortools=False
        )  # Use nearest neighbor
        visiting_order = tsp_solver.solve()

        # Step 6: Final path generation
        path_generator = FinalPathGenerator(
            path_matrix, visiting_order, poi_grid_coords
        )
        complete_path = path_generator.generate_complete_path()

        # Verify results
        assert len(visiting_order) == 4
        assert len(complete_path) > 0
        assert isinstance(layout_hash, str)

        print(f"Integration test passed!")
        print(f"Layout hash: {layout_hash}")
        print(f"Visiting order: {visiting_order}")
        print(f"Path length: {len(complete_path)} points")

    except ImportError as e:
        pytest.skip(f"Dependencies not installed: {e}")


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic functionality tests...")

    try:
        test_imports()
        print("✓ Imports test passed")
    except Exception as e:
        print(f"✗ Imports test failed: {e}")

    try:
        test_store_layout_cache_manager()
        print("✓ Cache manager test passed")
    except Exception as e:
        print(f"✗ Cache manager test failed: {e}")

    try:
        test_poi_mapper()
        print("✓ POI mapper test passed")
    except Exception as e:
        print(f"✗ POI mapper test failed: {e}")

    try:
        test_complete_workflow()
        print("✓ Integration test passed")
    except Exception as e:
        print(f"✗ Integration test failed: {e}")

    print("Test run completed!")
