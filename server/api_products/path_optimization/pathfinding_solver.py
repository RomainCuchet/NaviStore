"""
Pathfinding Solver utilisant la librairie pathfinding.

Alternative robuste et fiable à JPS pour le pathfinding dans les layouts de magasin.
Utilise les algorithmes A*, Dijkstra, et autres algorithmes éprouvés.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
import time

try:
    from pathfinding.core.grid import Grid
    from pathfinding.core.diagonal_movement import DiagonalMovement
    from pathfinding.finder.a_star import AStarFinder
    from pathfinding.finder.dijkstra import DijkstraFinder
    from pathfinding.finder.best_first import BestFirst
except ImportError:
    raise ImportError(
        "Librairie pathfinding requise. Installez avec: pip install pathfinding"
    )

from .utils import euclidean_distance, manhattan_distance

logger = logging.getLogger(__name__)


class PathfindingSolver:
    """
    Solver de pathfinding utilisant la librairie pathfinding.
    
    Compatible avec l'interface OptimizedJPS existante.
    Support des seuils de distance et optimisations de performance.
    """

    def __init__(
        self,
        grid_with_poi: np.ndarray,
        jps_cache: dict,  # Ignoré mais gardé pour compatibilité
        distance_threshold_grid: float,
        poi_coords: np.ndarray,
        algorithm: str = "astar",
        diagonal_movement: bool = True,
    ):
        """
        Initialize le solver pathfinding.

        Args:
            grid_with_poi: Grille avec POIs marqués (0=navigable, 1=POI, -1=obstacle)
            jps_cache: Cache JPS (ignoré, gardé pour compatibilité)
            distance_threshold_grid: Seuil de distance en unités de grille
            poi_coords: Coordonnées des POIs dans l'espace grille
            algorithm: Algorithme à utiliser ('astar', 'dijkstra', 'best_first')
            diagonal_movement: Autoriser les mouvements diagonaux
        """
        self.grid_array = grid_with_poi
        self.distance_threshold = distance_threshold_grid
        self.poi_coords = poi_coords
        self.grid_height, self.grid_width = grid_with_poi.shape
        self.algorithm = algorithm
        self.diagonal_movement = diagonal_movement

        # Créer le finder selon l'algorithme choisi
        self._create_finder()

        # Statistiques de performance
        self.stats = {
            "paths_computed": 0,
            "paths_failed": 0,
            "total_computation_time": 0.0,
            "average_path_length": 0.0,
            "cache_hits": 0,  # Toujours 0 (pas de cache)
            "cache_misses": 0,  # Toujours 0 (pas de cache)
            "algorithm_used": algorithm,
            "diagonal_enabled": diagonal_movement,
        }

        logger.info(
            f"Initialized PathfindingSolver with {len(poi_coords)} POIs, "
            f"threshold={distance_threshold_grid:.2f}, algorithm={algorithm}"
        )

    def _create_finder(self):
        """Crée le finder pathfinding selon l'algorithme choisi."""
        diagonal_mode = (
            DiagonalMovement.always if self.diagonal_movement 
            else DiagonalMovement.never
        )

        if self.algorithm == "astar":
            self.finder = AStarFinder(diagonal_movement=diagonal_mode)
        elif self.algorithm == "dijkstra":
            self.finder = DijkstraFinder(diagonal_movement=diagonal_mode)
        elif self.algorithm == "best_first":
            self.finder = BestFirst(diagonal_movement=diagonal_mode)
        else:
            raise ValueError(f"Algorithme non supporté: {self.algorithm}")

        logger.debug(f"Created {self.algorithm} finder with diagonal={self.diagonal_movement}")

    def find_path(
        self, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Trouve un chemin entre deux points.

        Args:
            start: Point de départ (x, y)
            goal: Point d'arrivée (x, y)

        Returns:
            Liste des coordonnées du chemin ou None si aucun chemin
        """
        try:
            start_time = time.time()
            
            # Créer une nouvelle grille pour chaque recherche (la méthode clone() n'existe pas)
            # Recréer la grille avec les mêmes données
            walkable_matrix = (self.grid_array >= 0).astype(int)
            grid = Grid(matrix=walkable_matrix)
            
            # Obtenir les nœuds start et goal
            # CORRECTION: pathfinding lib utilise node(x, y) où x=col, y=row
            # Nos coordonnées sont (row, col), donc il faut inverser
            start_node = grid.node(start[1], start[0])  # (col, row)
            goal_node = grid.node(goal[1], goal[0])    # (col, row)
            
            # Vérifier que les nœuds sont walkable
            if not start_node.walkable or not goal_node.walkable:
                logger.debug(f"Start {start} ou goal {goal} non walkable")
                return None
            
            # Recherche de chemin
            path, runs = self.finder.find_path(start_node, goal_node, grid)
            
            computation_time = time.time() - start_time
            self.stats["total_computation_time"] += computation_time
            
            if path:
                # Convertir en liste de tuples (row, col)
                # CORRECTION: node.x=col, node.y=row, donc il faut inverser
                path_coords = [(node.y, node.x) for node in path]  # (row, col)
                self.stats["paths_computed"] += 1
                
                # Mettre à jour moyenne longueur de chemin
                total_paths = self.stats["paths_computed"]
                current_avg = self.stats["average_path_length"]
                new_length = len(path_coords)
                self.stats["average_path_length"] = (
                    (current_avg * (total_paths - 1) + new_length) / total_paths
                )
                
                logger.debug(
                    f"Path found: {start} -> {goal}, length={len(path_coords)}, "
                    f"time={computation_time:.4f}s"
                )
                return path_coords
            else:
                self.stats["paths_failed"] += 1
                logger.debug(f"No path found: {start} -> {goal}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du pathfinding {start} -> {goal}: {e}")
            self.stats["paths_failed"] += 1
            return None

    def compute_all_paths(
        self,
    ) -> Tuple[np.ndarray, List[List[Optional[List[Tuple[int, int]]]]]]:
        """
        Calcule toutes les distances et chemins entre POIs.

        Returns:
            Tuple de (matrice_distances, matrice_chemins)
        """
        logger.info(f"Computing all paths with {self.algorithm.upper()} pathfinding...")
        start_time = time.time()

        n_pois = len(self.poi_coords)
        distance_matrix = np.full((n_pois, n_pois), np.inf)
        path_matrix = [[None for _ in range(n_pois)] for _ in range(n_pois)]

        paths_computed = 0
        paths_failed = 0
        paths_skipped_threshold = 0

        for i in range(n_pois):
            for j in range(n_pois):
                if i == j:
                    # Distance à soi-même = 0
                    distance_matrix[i, j] = 0
                    path_matrix[i][j] = [tuple(self.poi_coords[i])]
                    continue

                start = tuple(self.poi_coords[i])
                goal = tuple(self.poi_coords[j])

                # Vérifier le seuil de distance euclidienne
                euclidean_dist = euclidean_distance(start, goal)
                if euclidean_dist > self.distance_threshold:
                    paths_skipped_threshold += 1
                    logger.debug(
                        f"Skipping {start} -> {goal}: distance {euclidean_dist:.2f} > threshold {self.distance_threshold:.2f}"
                    )
                    continue

                # Rechercher le chemin
                path = self.find_path(start, goal)

                if path:
                    # Calculer la distance réelle du chemin
                    path_length = 0
                    for k in range(len(path) - 1):
                        path_length += euclidean_distance(path[k], path[k + 1])

                    distance_matrix[i, j] = path_length
                    path_matrix[i][j] = path
                    paths_computed += 1
                else:
                    paths_failed += 1

        total_time = time.time() - start_time

        logger.info(
            f"{self.algorithm.upper()} pathfinding completed: "
            f"{paths_computed} paths found, {paths_failed} failed, "
            f"{paths_skipped_threshold} skipped (threshold), "
            f"total_time={total_time:.3f}s"
        )

        # Mettre à jour les statistiques globales
        self.stats["total_paths_computed"] = paths_computed
        self.stats["total_paths_failed"] = paths_failed
        self.stats["paths_skipped_threshold"] = paths_skipped_threshold
        self.stats["total_algorithm_time"] = total_time

        return distance_matrix, path_matrix

    def get_optimization_stats(self) -> Dict:
        """
        Retourne les statistiques d'optimisation.
        Compatible avec l'interface OptimizedJPS.
        """
        total_paths = self.stats["paths_computed"] + self.stats["paths_failed"]
        success_rate = (
            self.stats["paths_computed"] / total_paths if total_paths > 0 else 0
        )

        return {
            "algorithm": self.algorithm,
            "diagonal_movement": self.diagonal_movement,
            "grid_size": f"{self.grid_width}x{self.grid_height}",
            "total_pois": len(self.poi_coords),
            "distance_threshold": self.distance_threshold,
            "paths_computed": self.stats.get("total_paths_computed", 0),
            "paths_failed": self.stats.get("total_paths_failed", 0),
            "paths_skipped_threshold": self.stats.get("paths_skipped_threshold", 0),
            "success_rate": f"{success_rate:.2%}",
            "average_path_length": f"{self.stats['average_path_length']:.2f}",
            "total_computation_time": f"{self.stats['total_computation_time']:.3f}s",
            "total_algorithm_time": f"{self.stats.get('total_algorithm_time', 0):.3f}s",
            # Compatibilité avec JPS (toujours 0)
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_hit_rate": "0.0%",
        }

    def get_pathfinding_info(self) -> Dict:
        """Retourne des informations détaillées sur le solver."""
        return {
            "solver_type": "pathfinding_library",
            "algorithm": self.algorithm,
            "version": "pathfinding2",
            "features": {
                "diagonal_movement": self.diagonal_movement,
                "algorithms_available": ["astar", "dijkstra", "best_first"],
                "distance_thresholding": True,
                "grid_validation": True,
                "performance_stats": True,
            },
            "grid_info": {
                "width": self.grid_width,
                "height": self.grid_height,
                "total_cells": self.grid_width * self.grid_height,
                "walkable_cells": int(np.sum(self.grid_array != -1)),
                "obstacle_cells": int(np.sum(self.grid_array == -1)),
            },
        }


# Classe d'usine pour créer le bon solver
class PathfindingSolverFactory:
    """Factory pour créer des solvers pathfinding avec différents algorithmes."""

    @staticmethod
    def create_solver(
        grid_with_poi: np.ndarray,
        jps_cache: dict,
        distance_threshold_grid: float,
        poi_coords: np.ndarray,
        algorithm: str = "astar",
        diagonal_movement: bool = True,
    ) -> PathfindingSolver:
        """
        Crée un solver pathfinding.

        Args:
            grid_with_poi: Grille avec POIs
            jps_cache: Cache (ignoré)
            distance_threshold_grid: Seuil de distance
            poi_coords: Coordonnées POIs
            algorithm: Algorithme ('astar', 'dijkstra', 'best_first')
            diagonal_movement: Autoriser diagonales

        Returns:
            PathfindingSolver configuré
        """
        return PathfindingSolver(
            grid_with_poi=grid_with_poi,
            jps_cache=jps_cache,
            distance_threshold_grid=distance_threshold_grid,
            poi_coords=poi_coords,
            algorithm=algorithm,
            diagonal_movement=diagonal_movement,
        )

    @staticmethod
    def get_available_algorithms() -> List[str]:
        """Retourne la liste des algorithmes disponibles."""
        return ["astar", "dijkstra", "best_first"]

    @staticmethod
    def get_recommended_algorithm(grid_size: int, poi_count: int) -> str:
        """
        Recommande un algorithme basé sur la taille de grille et nombre de POIs.

        Args:
            grid_size: Taille de la grille (width * height)
            poi_count: Nombre de POIs

        Returns:
            Nom de l'algorithme recommandé
        """
        if grid_size > 10000 and poi_count > 20:
            return "best_first"  # Plus rapide pour grandes grilles
        elif poi_count > 50:
            return "dijkstra"  # Plus fiable pour beaucoup de POIs
        else:
            return "astar"  # Équilibré pour cas généraux