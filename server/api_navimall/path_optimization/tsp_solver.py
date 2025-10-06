"""
TSP Solver using Google OR-Tools for optimal route computation.

Solves the Traveling Salesman Problem to find optimal visiting order.
"""

import numpy as np
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp

    ORTOOLS_AVAILABLE = True
except ImportError:
    logger.warning(
        "OR-Tools not available, will use fallback nearest neighbor algorithm"
    )
    ORTOOLS_AVAILABLE = False


class TSPSolver:
    """
    Solves the Traveling Salesman Problem using Google OR-Tools or fallback algorithm.

    Computes optimal route visiting all points of interest.
    """

    def __init__(
        self,
        distance_matrix: np.ndarray,
        max_runtime: int = 60,
        solution_gap: float = 0.01,
        use_ortools: bool = True,
    ):
        """
        Initialize the TSP solver.

        Args:
            distance_matrix: Distance matrix between POIs
            max_runtime: Maximum runtime in seconds
            solution_gap: Solution gap tolerance (0.01 = 1%)
            use_ortools: Whether to use OR-Tools (if available)
        """
        self.distance_matrix = distance_matrix
        self.max_runtime = max_runtime
        self.solution_gap = solution_gap
        self.use_ortools = use_ortools and ORTOOLS_AVAILABLE
        self.n_locations = len(distance_matrix)

        logger.info(
            f"Initialized TSP solver for {self.n_locations} locations, "
            f"using {'OR-Tools' if self.use_ortools else 'nearest neighbor'}"
        )

    def _validate_distance_matrix(self) -> None:
        """
        Validate the distance matrix for TSP solving.

        Raises:
            ValueError: If distance matrix is invalid
        """
        if self.distance_matrix.shape[0] != self.distance_matrix.shape[1]:
            raise ValueError("Distance matrix must be square")

        if self.n_locations < 2:
            raise ValueError("Need at least 2 locations for TSP")

        # Check for infinite distances on diagonal
        for i in range(self.n_locations):
            if not np.isfinite(self.distance_matrix[i, i]):
                raise ValueError(f"Diagonal element [{i}, {i}] must be finite")

    def _create_distance_callback(self, distance_matrix: np.ndarray):
        """
        Create distance callback for OR-Tools.

        Args:
            distance_matrix: Distance matrix to use

        Returns:
            Distance callback function
        """

        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)

            distance = distance_matrix[from_node][to_node]

            # Convert infinite distances to large finite values
            if not np.isfinite(distance):
                return int(1e6)  # Large penalty for unreachable locations

            return int(distance * 1000)  # Scale to integer (millimeters)

        # This will be bound to the manager when called
        return distance_callback

    def solve_with_ortools(self) -> List[int]:
        """
        Solve TSP using Google OR-Tools.

        Returns:
            List of location indices representing the optimal tour

        Raises:
            RuntimeError: If OR-Tools fails to find a solution
        """
        logger.info("Solving TSP with OR-Tools...")

        # Create the routing index manager
        manager = pywrapcp.RoutingIndexManager(self.n_locations, 1, 0)

        # Create routing model
        routing = pywrapcp.RoutingModel(manager)

        # Create distance callback
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)

            distance = self.distance_matrix[from_node][to_node]

            # Convert infinite distances to large finite values
            if not np.isfinite(distance):
                return int(1e6)  # Large penalty for unreachable locations

            return int(distance * 1000)  # Scale to integer (millimeters)

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = self.max_runtime
        search_parameters.solution_limit = 100

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            # Extract the route
            route = []
            index = routing.Start(0)

            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))

            total_distance = (
                solution.ObjectiveValue() / 1000.0
            )  # Convert back from millimeters

            logger.info(
                f"OR-Tools solution found: distance={total_distance:.2f}, route length={len(route)}"
            )
            return route
        else:
            raise RuntimeError("OR-Tools failed to find a solution")

    def solve_with_nearest_neighbor(self, start_location: int = 0) -> List[int]:
        """
        Solve TSP using nearest neighbor heuristic.

        Args:
            start_location: Starting location index

        Returns:
            List of location indices representing the tour
        """
        logger.info("Solving TSP with nearest neighbor heuristic...")

        unvisited = set(range(self.n_locations))
        route = [start_location]
        unvisited.remove(start_location)

        current_location = start_location
        total_distance = 0

        while unvisited:
            # Find nearest unvisited location
            nearest_location = None
            nearest_distance = float("inf")

            for location in unvisited:
                distance = self.distance_matrix[current_location][location]
                if np.isfinite(distance) and distance < nearest_distance:
                    nearest_distance = distance
                    nearest_location = location

            if nearest_location is None:
                # No reachable location found, pick any remaining
                nearest_location = next(iter(unvisited))
                nearest_distance = float("inf")

            route.append(nearest_location)
            unvisited.remove(nearest_location)
            total_distance += nearest_distance
            current_location = nearest_location

        logger.info(
            f"Nearest neighbor solution: distance={total_distance:.2f}, route length={len(route)}"
        )
        return route

    def solve(self) -> List[int]:
        """
        Solve the TSP using the best available algorithm.

        Returns:
            List of location indices representing the optimal tour

        Raises:
            ValueError: If distance matrix is invalid
            RuntimeError: If no solution can be found
        """
        self._validate_distance_matrix()

        try:
            if self.use_ortools:
                return self.solve_with_ortools()
            else:
                return self.solve_with_nearest_neighbor()
        except Exception as e:
            logger.warning(f"Primary TSP solver failed: {str(e)}, trying fallback")
            # Fallback to nearest neighbor if OR-Tools fails
            if self.use_ortools:
                return self.solve_with_nearest_neighbor()
            else:
                raise RuntimeError(f"TSP solving failed: {str(e)}")

    def compute_tour_distance(self, tour: List[int]) -> float:
        """
        Compute total distance for a given tour.

        Args:
            tour: List of location indices

        Returns:
            Total tour distance
        """
        if len(tour) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(len(tour)):
            current = tour[i]
            next_loc = tour[(i + 1) % len(tour)]  # Wrap around for closed tour

            distance = self.distance_matrix[current][next_loc]
            if np.isfinite(distance):
                total_distance += distance
            else:
                return float("inf")  # Invalid tour

        return total_distance

    def optimize_tour_order(
        self, initial_tour: List[int], max_iterations: int = 1000
    ) -> List[int]:
        """
        Optimize tour using 2-opt local search.

        Args:
            initial_tour: Initial tour to optimize
            max_iterations: Maximum optimization iterations

        Returns:
            Optimized tour
        """
        if len(initial_tour) < 4:
            return initial_tour

        current_tour = initial_tour.copy()
        current_distance = self.compute_tour_distance(current_tour)

        logger.info(
            f"Starting 2-opt optimization, initial distance: {current_distance:.2f}"
        )

        improved = True
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False

            for i in range(len(current_tour) - 1):
                for j in range(i + 2, len(current_tour)):
                    # Avoid adjacent edges and wrapping
                    if j == len(current_tour) - 1 and i == 0:
                        continue

                    # Create new tour by reversing segment between i+1 and j
                    new_tour = current_tour.copy()
                    new_tour[i + 1 : j + 1] = reversed(new_tour[i + 1 : j + 1])

                    new_distance = self.compute_tour_distance(new_tour)

                    if new_distance < current_distance:
                        current_tour = new_tour
                        current_distance = new_distance
                        improved = True
                        logger.debug(
                            f"Improved tour at iteration {iteration}, new distance: {current_distance:.2f}"
                        )

            iteration += 1

        logger.info(
            f"2-opt optimization completed after {iteration} iterations, "
            f"final distance: {current_distance:.2f}"
        )

        return current_tour

    def get_solver_info(self) -> Dict[str, Any]:
        """
        Get information about the TSP solver configuration.

        Returns:
            Dictionary with solver information
        """
        return {
            "n_locations": self.n_locations,
            "max_runtime": self.max_runtime,
            "solution_gap": self.solution_gap,
            "using_ortools": self.use_ortools,
            "ortools_available": ORTOOLS_AVAILABLE,
            "distance_matrix_shape": self.distance_matrix.shape,
            "finite_distances": int(np.sum(np.isfinite(self.distance_matrix))),
            "infinite_distances": int(np.sum(~np.isfinite(self.distance_matrix))),
        }
