#!/usr/bin/env python3
"""
Simulateur A* Indépendant - NaviStore

Simulateur spécialisé pour visualiser l'algorithme A* sur des grilles H5.
Interface graphique dédiée avec visualisation pas-à-pas et saisie de coordonnées.

Fonctionnalités:
- Chargement de grilles H5
- Visualisation A* temps réel
- Clic pour sélectionner start/goal
- Saisie manuelle de coordonnées
- Animation pas-à-pas
- Statistiques détaillées
"""

import pygame
import numpy as np
import h5py
import sys
import os
import time
from typing import Tuple, Optional, List, Dict, Set
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import heapq
from dataclasses import dataclass
from enum import Enum

# Ajouter le chemin vers les modules NaviStore
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from api_navimall.path_optimization import load_layout_from_h5

    NAVISTORE_AVAILABLE = True
except ImportError:
    NAVISTORE_AVAILABLE = False
    print("⚠️ Modules NaviStore non disponibles - mode standalone")

# Configuration des couleurs
COLORS = {
    # Grille de base
    "navigable": (255, 255, 255),  # Blanc - zone libre
    "obstacle": (0, 0, 0),  # Noir - obstacle
    "poi": (0, 200, 0),  # Vert - POI
    "grid_line": (200, 200, 200),  # Gris clair - lignes
    # Pathfinding A*
    "start": (255, 0, 0),  # Rouge - point de départ
    "goal": (0, 0, 255),  # Bleu - point d'arrivée
    "open_set": (255, 255, 0),  # Jaune - nœuds à explorer
    "closed_set": (255, 165, 0),  # Orange - nœuds explorés
    "path": (255, 0, 255),  # Magenta - chemin final
    "current": (0, 255, 255),  # Cyan - nœud en cours
    # Interface
    "background": (240, 240, 240),  # Gris très clair
    "ui_bg": (220, 220, 220),  # Gris clair - panneaux
    "text": (0, 0, 0),  # Noir - texte
    "button": (180, 180, 180),  # Gris - boutons
    "button_hover": (160, 160, 160),  # Gris foncé - survol
    "button_active": (100, 150, 255),  # Bleu - bouton actif
}


class SimulationState(Enum):
    """États de la simulation."""

    IDLE = "idle"  # En attente
    SELECTING_START = "selecting_start"  # Sélection point départ
    SELECTING_GOAL = "selecting_goal"  # Sélection point arrivée
    READY = "ready"  # Prêt à calculer
    RUNNING = "running"  # Calcul en cours
    PAUSED = "paused"  # En pause
    FINISHED = "finished"  # Terminé


@dataclass
class AStarNode:
    """Nœud pour l'algorithme A*."""

    x: int
    y: int
    g_cost: float = float("inf")  # Coût depuis le début
    h_cost: float = 0  # Heuristique vers la fin
    f_cost: float = float("inf")  # g_cost + h_cost
    parent: Optional["AStarNode"] = None

    def __lt__(self, other):
        return self.f_cost < other.f_cost


class AStarVisualizer:
    """Visualiseur A* avec animation pas-à-pas."""

    def __init__(self, grid: np.ndarray):
        """
        Initialise le visualiseur A*.

        Args:
            grid: Grille numpy (0=libre, -1=obstacle, 1=POI)
        """
        self.grid = grid
        self.height, self.width = grid.shape

        # État de la simulation
        self.start_pos = None
        self.goal_pos = None
        self.current_node = None

        # Structures A*
        self.open_set: List[AStarNode] = []
        self.closed_set: Set[Tuple[int, int]] = set()
        self.nodes: Dict[Tuple[int, int], AStarNode] = {}
        self.final_path: List[Tuple[int, int]] = []

        # Statistiques
        self.stats = {
            "nodes_explored": 0,
            "nodes_in_queue": 0,
            "path_length": 0,
            "computation_time": 0.0,
            "path_distance": 0.0,
            "iterations": 0,
        }

        # Animation
        self.animation_speed = 50  # ms entre les étapes
        self.show_costs = True
        self.show_heuristic = False

    def reset(self):
        """Remet à zéro la simulation."""
        self.start_pos = None
        self.goal_pos = None
        self.current_node = None
        self.open_set.clear()
        self.closed_set.clear()
        self.nodes.clear()
        self.final_path.clear()

        # Reset stats
        for key in self.stats:
            self.stats[key] = 0

    def set_start(self, pos: Tuple[int, int]) -> bool:
        """Définit le point de départ."""
        x, y = pos
        if 0 <= x < self.height and 0 <= y < self.width and self.grid[x, y] != -1:
            self.start_pos = pos
            return True
        return False

    def set_goal(self, pos: Tuple[int, int]) -> bool:
        """Définit le point d'arrivée."""
        x, y = pos
        if 0 <= x < self.height and 0 <= y < self.width and self.grid[x, y] != -1:
            self.goal_pos = pos
            return True
        return False

    def heuristic(self, pos: Tuple[int, int]) -> float:
        """Calcule l'heuristique (distance de Manhattan)."""
        if not self.goal_pos:
            return 0
        return abs(pos[0] - self.goal_pos[0]) + abs(pos[1] - self.goal_pos[1])

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Obtient les voisins valides d'une position."""
        x, y = pos
        neighbors = []

        # 8-connectivité (diagonales autorisées)
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if (
                0 <= nx < self.height
                and 0 <= ny < self.width
                and self.grid[nx, ny] != -1
            ):
                neighbors.append((nx, ny))

        return neighbors

    def calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calcule la distance entre deux positions."""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])

        # Distance euclidienne pour les diagonales
        return np.sqrt(dx * dx + dy * dy)

    def initialize_search(self):
        """Initialise la recherche A*."""
        if not self.start_pos or not self.goal_pos:
            return False

        # Créer le nœud de départ
        start_node = AStarNode(
            x=self.start_pos[0],
            y=self.start_pos[1],
            g_cost=0,
            h_cost=self.heuristic(self.start_pos),
        )
        start_node.f_cost = start_node.g_cost + start_node.h_cost

        # Initialiser les structures
        self.open_set = [start_node]
        self.closed_set.clear()
        self.nodes = {self.start_pos: start_node}
        self.final_path.clear()

        # Reset stats
        self.stats = {
            "nodes_explored": 0,
            "nodes_in_queue": 1,
            "path_length": 0,
            "computation_time": 0.0,
            "path_distance": 0.0,
            "iterations": 0,
        }

        return True

    def step(self) -> bool:
        """Effectue une étape de l'algorithme A*. Retourne True si fini."""
        if not self.open_set:
            return True  # Échec - pas de chemin

        # Prendre le nœud avec le plus petit f_cost
        heapq.heapify(self.open_set)
        current = heapq.heappop(self.open_set)
        self.current_node = current

        current_pos = (current.x, current.y)
        self.closed_set.add(current_pos)
        self.stats["nodes_explored"] += 1
        self.stats["iterations"] += 1

        # Vérifier si on a atteint le goal
        if current_pos == self.goal_pos:
            self._reconstruct_path(current)
            return True  # Succès

        # Explorer les voisins
        for neighbor_pos in self.get_neighbors(current_pos):
            if neighbor_pos in self.closed_set:
                continue

            # Calculer le nouveau g_cost
            tentative_g_cost = current.g_cost + self.calculate_distance(
                current_pos, neighbor_pos
            )

            # Créer ou récupérer le nœud voisin
            if neighbor_pos not in self.nodes:
                neighbor = AStarNode(
                    x=neighbor_pos[0],
                    y=neighbor_pos[1],
                    h_cost=self.heuristic(neighbor_pos),
                )
                self.nodes[neighbor_pos] = neighbor
            else:
                neighbor = self.nodes[neighbor_pos]

            # Si ce chemin est meilleur
            if tentative_g_cost < neighbor.g_cost:
                neighbor.parent = current
                neighbor.g_cost = tentative_g_cost
                neighbor.f_cost = neighbor.g_cost + neighbor.h_cost

                # Ajouter à open_set si pas déjà présent
                if neighbor not in self.open_set:
                    heapq.heappush(self.open_set, neighbor)

        self.stats["nodes_in_queue"] = len(self.open_set)
        return False  # Continue

    def _reconstruct_path(self, goal_node: AStarNode):
        """Reconstruit le chemin depuis le goal jusqu'au start."""
        path = []
        current = goal_node

        while current:
            path.append((current.x, current.y))
            current = current.parent

        self.final_path = list(reversed(path))
        self.stats["path_length"] = len(self.final_path)

        # Calculer la distance du chemin
        if len(self.final_path) > 1:
            distance = 0
            for i in range(len(self.final_path) - 1):
                distance += self.calculate_distance(
                    self.final_path[i], self.final_path[i + 1]
                )
            self.stats["path_distance"] = distance

    def run_complete(self) -> bool:
        """Exécute l'algorithme complet d'un coup."""
        if not self.initialize_search():
            return False

        start_time = time.time()

        while True:
            if self.step():
                break

        self.stats["computation_time"] = (time.time() - start_time) * 1000
        return len(self.final_path) > 0


class AStarSimulator:
    """Simulateur principal avec interface Pygame."""

    def __init__(self):
        """Initialise le simulateur."""
        pygame.init()

        # Configuration de base
        self.cell_size = 30
        self.min_cell_size = 15
        self.max_cell_size = 60
        self.ui_panel_width = 400
        self.ui_height = 100

        # État de l'application
        self.running = True
        self.state = SimulationState.IDLE
        self.grid = None
        self.edge_length = 100.0
        self.visualizer = None

        # Interface
        self.screen = None
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font = pygame.font.Font(None, 16)
        self.buttons = []

        # Animation
        self.auto_step = False
        self.step_delay = 100  # ms
        self.last_step_time = 0

        # Options d'affichage
        self.show_coordinates = True
        self.show_costs = True
        self.show_grid_lines = True

        self._create_default_grid()
        self._setup_window()

        print("🎯 Simulateur A* NaviStore initialisé")
        print("Contrôles:")
        print("  Clic gauche: Sélectionner start/goal")
        print("  ESPACE: Étape suivante")
        print("  R: Reset simulation")
        print("  A: Auto/Manuel")
        print("  +/-: Zoom")

    def _create_default_grid(self):
        """Crée une grille par défaut pour les tests."""
        self.grid = np.zeros((15, 20), dtype=int)

        # Ajouter quelques obstacles pour tester
        self.grid[3:6, 5:8] = -1  # Bloc obstacle
        self.grid[8:11, 12:15] = -1  # Autre bloc
        self.grid[5:8, 15] = -1  # Mur vertical

        # Quelques POIs
        self.grid[2, 2] = 1
        self.grid[12, 18] = 1

        self.visualizer = AStarVisualizer(self.grid)
        self.state = SimulationState.SELECTING_START

    def _setup_window(self):
        """Configure la fenêtre principale."""
        if self.grid is None:
            return

        height, width = self.grid.shape

        # Calculer dimensions
        grid_width = width * self.cell_size
        grid_height = height * self.cell_size

        window_width = grid_width + self.ui_panel_width + 40
        window_height = max(grid_height + self.ui_height + 40, 600)

        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Simulateur A* - NaviStore")

        self._create_buttons()

    def _create_buttons(self):
        """Crée les boutons de l'interface."""
        if not self.screen:
            return

        button_y = self.screen.get_height() - 70
        button_configs = [
            ("Charger H5", self._load_h5_file, 20),
            ("Coordonnées", self._input_coordinates, 120),
            ("Reset", self._reset_simulation, 240),
            ("Étape", self._manual_step, 320),
            ("Auto", self._toggle_auto, 400),
            ("Complet", self._run_complete, 480),
            ("Options", self._show_options, 580),
            ("Aide", self._show_help, 660),
        ]

        self.buttons = []
        for text, callback, x in button_configs:
            button = {
                "rect": pygame.Rect(x, button_y, 80, 30),
                "text": text,
                "callback": callback,
                "hovered": False,
            }
            self.buttons.append(button)

    def _load_h5_file(self):
        """Charge un fichier H5."""
        root = tk.Tk()
        root.withdraw()

        try:
            file_path = filedialog.askopenfilename(
                title="Charger grille H5",
                filetypes=[("Fichiers HDF5", "*.h5"), ("Tous fichiers", "*.*")],
                initialdir=os.path.join(
                    os.path.dirname(__file__), "..", "..", "assets", "layout_examples"
                ),
            )

            if file_path:
                if NAVISTORE_AVAILABLE:
                    # Utiliser la fonction NaviStore
                    layout, edge_length = load_layout_from_h5(file_path)
                else:
                    # Lecture manuelle
                    with h5py.File(file_path, "r") as f:
                        layout = np.array(f["layout"])
                        edge_length = float(f["edge_length"][()])

                self.grid = layout
                self.edge_length = edge_length
                self.visualizer = AStarVisualizer(self.grid)
                self.state = SimulationState.SELECTING_START
                self._setup_window()

                filename = os.path.basename(file_path)
                print(f"✅ Grille chargée: {filename} ({layout.shape})")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            root.destroy()

    def _input_coordinates(self):
        """Saisie manuelle des coordonnées."""
        if not self.visualizer:
            return

        root = tk.Tk()
        root.withdraw()

        try:
            # Demander les coordonnées de départ
            start_input = simpledialog.askstring(
                "Coordonnées de départ",
                f"Entrez les coordonnées de départ (x,y):\nRange: x=0-{self.grid.shape[0]-1}, y=0-{self.grid.shape[1]-1}",
            )

            if start_input:
                start_x, start_y = map(int, start_input.split(","))

                if self.visualizer.set_start((start_x, start_y)):
                    # Demander les coordonnées d'arrivée
                    goal_input = simpledialog.askstring(
                        "Coordonnées d'arrivée",
                        f"Entrez les coordonnées d'arrivée (x,y):\nRange: x=0-{self.grid.shape[0]-1}, y=0-{self.grid.shape[1]-1}",
                    )

                    if goal_input:
                        goal_x, goal_y = map(int, goal_input.split(","))

                        if self.visualizer.set_goal((goal_x, goal_y)):
                            self.state = SimulationState.READY
                            print(
                                f"🎯 Coordonnées définies: Départ({start_x},{start_y}) → Arrivée({goal_x},{goal_y})"
                            )
                        else:
                            messagebox.showerror(
                                "Erreur",
                                f"Coordonnées d'arrivée invalides: ({goal_x}, {goal_y})",
                            )
                else:
                    messagebox.showerror(
                        "Erreur",
                        f"Coordonnées de départ invalides: ({start_x}, {start_y})",
                    )

        except ValueError:
            messagebox.showerror("Erreur", "Format invalide. Utilisez: x,y")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {str(e)}")
        finally:
            root.destroy()

    def _reset_simulation(self):
        """Remet à zéro la simulation."""
        if self.visualizer:
            self.visualizer.reset()
        self.state = SimulationState.SELECTING_START
        self.auto_step = False
        print("🔄 Simulation remise à zéro")

    def _manual_step(self):
        """Effectue une étape manuelle."""
        if self.state == SimulationState.READY:
            if self.visualizer.initialize_search():
                self.state = SimulationState.RUNNING

        if self.state == SimulationState.RUNNING:
            if self.visualizer.step():
                self.state = SimulationState.FINISHED
                print("🏁 Simulation terminée")

    def _toggle_auto(self):
        """Active/désactive le mode automatique."""
        self.auto_step = not self.auto_step
        if self.auto_step and self.state == SimulationState.READY:
            if self.visualizer.initialize_search():
                self.state = SimulationState.RUNNING
        print(f"🤖 Mode automatique: {'ON' if self.auto_step else 'OFF'}")

    def _run_complete(self):
        """Exécute l'algorithme complet."""
        if self.state in [SimulationState.READY, SimulationState.RUNNING]:
            success = self.visualizer.run_complete()
            self.state = SimulationState.FINISHED

            if success:
                print("✅ Chemin trouvé!")
                print(f"   Longueur: {self.visualizer.stats['path_length']} points")
                print(f"   Distance: {self.visualizer.stats['path_distance']:.2f}")
                print(f"   Temps: {self.visualizer.stats['computation_time']:.2f}ms")
                print(f"   Nœuds explorés: {self.visualizer.stats['nodes_explored']}")
            else:
                print("❌ Aucun chemin trouvé")

    def _show_options(self):
        """Affiche les options."""
        # Toggle des options d'affichage
        self.show_coordinates = not self.show_coordinates
        self.show_costs = not self.show_costs
        self.show_grid_lines = not self.show_grid_lines

        print(
            f"🎛️ Options: Coordonnées={self.show_coordinates}, Coûts={self.show_costs}, Grille={self.show_grid_lines}"
        )

    def _show_help(self):
        """Affiche l'aide."""
        help_text = """
SIMULATEUR A* - AIDE

CHARGEMENT:
• Bouton 'Charger H5': Ouvrir fichier layout
• Grille par défaut disponible au démarrage

SÉLECTION DES POINTS:
• Clic gauche: Sélectionner départ puis arrivée
• Bouton 'Coordonnées': Saisie manuelle (x,y)

SIMULATION:
• Bouton 'Étape': Exécution pas-à-pas
• Bouton 'Auto': Mode automatique
• Bouton 'Complet': Calcul instantané
• ESPACE: Étape suivante (clavier)

CONTRÔLES:
• R: Reset simulation
• A: Toggle auto/manuel
• +/-: Zoom avant/arrière
• ESC: Quitter

VISUALISATION:
• Rouge: Point de départ
• Bleu: Point d'arrivée
• Jaune: Nœuds en attente (open set)
• Orange: Nœuds explorés (closed set)
• Cyan: Nœud en cours d'exploration
• Magenta: Chemin final

STATISTIQUES:
Affichage temps réel des métriques A*
dans le panneau de droite.
        """

        root = tk.Tk()
        root.withdraw()
        try:
            messagebox.showinfo("Aide - Simulateur A*", help_text)
        finally:
            root.destroy()

    def _get_grid_pos(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Convertit position souris en coordonnées grille."""
        if not self.grid is not None:
            return None

        mx, my = mouse_pos

        # Offset pour centrer la grille
        offset_x = 20
        offset_y = 20

        col = (mx - offset_x) // self.cell_size
        row = (my - offset_y) // self.cell_size

        height, width = self.grid.shape
        if 0 <= row < height and 0 <= col < width:
            return (row, col)
        return None

    def _handle_click(self, pos: Tuple[int, int]):
        """Gère les clics de souris."""
        # Vérifier clics sur boutons
        for button in self.buttons:
            if button["rect"].collidepoint(pos):
                button["callback"]()
                return

        # Gestion des clics sur la grille
        grid_pos = self._get_grid_pos(pos)
        if grid_pos and self.visualizer:
            row, col = grid_pos

            # Vérifier que la cellule est libre
            if self.grid[row, col] == -1:
                print(f"❌ Impossible de sélectionner un obstacle en ({row}, {col})")
                return

            if self.state == SimulationState.SELECTING_START:
                if self.visualizer.set_start((row, col)):
                    self.state = SimulationState.SELECTING_GOAL
                    print(
                        f"🚀 Départ sélectionné: ({row}, {col}) - Cliquez pour l'arrivée"
                    )

            elif self.state == SimulationState.SELECTING_GOAL:
                if (row, col) == self.visualizer.start_pos:
                    print("⚠️ L'arrivée doit être différente du départ")
                    return

                if self.visualizer.set_goal((row, col)):
                    self.state = SimulationState.READY
                    print(f"🎯 Arrivée sélectionnée: ({row}, {col}) - Prêt à simuler!")

            elif self.state in [SimulationState.FINISHED, SimulationState.READY]:
                # Recommencer
                self._reset_simulation()
                if self.visualizer.set_start((row, col)):
                    self.state = SimulationState.SELECTING_GOAL
                    print(f"🚀 Nouveau départ: ({row}, {col}) - Cliquez pour l'arrivée")

    def _handle_keyboard(self, key):
        """Gère les entrées clavier."""
        if key == pygame.K_SPACE:
            self._manual_step()
        elif key == pygame.K_r:
            self._reset_simulation()
        elif key == pygame.K_a:
            self._toggle_auto()
        elif key == pygame.K_c:
            self._run_complete()
        elif key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            if self.cell_size < self.max_cell_size:
                self.cell_size += 3
                self._setup_window()
        elif key == pygame.K_MINUS:
            if self.cell_size > self.min_cell_size:
                self.cell_size -= 3
                self._setup_window()
        elif key == pygame.K_o:
            self._show_options()
        elif key == pygame.K_h or key == pygame.K_F1:
            self._show_help()

    def _draw_grid(self):
        """Dessine la grille principale."""
        if not self.grid is not None or not self.screen:
            return

        height, width = self.grid.shape
        offset_x, offset_y = 20, 20

        # Dessiner les cellules
        for row in range(height):
            for col in range(width):
                x = offset_x + col * self.cell_size
                y = offset_y + row * self.cell_size

                cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

                # Couleur de base selon le type de cellule
                cell_value = self.grid[row, col]
                if cell_value == -1:
                    color = COLORS["obstacle"]
                elif cell_value == 1:
                    color = COLORS["poi"]
                else:
                    color = COLORS["navigable"]

                # Superposition pour A*
                pos = (row, col)
                if self.visualizer:
                    if pos == self.visualizer.start_pos:
                        color = COLORS["start"]
                    elif pos == self.visualizer.goal_pos:
                        color = COLORS["goal"]
                    elif pos in self.visualizer.closed_set:
                        color = COLORS["closed_set"]
                    elif self.visualizer.current_node and pos == (
                        self.visualizer.current_node.x,
                        self.visualizer.current_node.y,
                    ):
                        color = COLORS["current"]
                    elif any(
                        node
                        for node in self.visualizer.open_set
                        if (node.x, node.y) == pos
                    ):
                        color = COLORS["open_set"]
                    elif pos in self.visualizer.final_path:
                        color = COLORS["path"]

                pygame.draw.rect(self.screen, color, cell_rect)

                # Lignes de grille
                if self.show_grid_lines:
                    pygame.draw.rect(self.screen, COLORS["grid_line"], cell_rect, 1)

                # Affichage des coordonnées
                if self.show_coordinates and self.cell_size >= 25:
                    coord_text = self.tiny_font.render(
                        f"{row},{col}", True, (100, 100, 100)
                    )
                    self.screen.blit(coord_text, (x + 2, y + 2))

                # Affichage des coûts A*
                if (
                    self.show_costs
                    and self.cell_size >= 30
                    and self.visualizer
                    and pos in self.visualizer.nodes
                ):
                    node = self.visualizer.nodes[pos]
                    if node.g_cost != float("inf"):
                        cost_text = self.tiny_font.render(
                            f"f:{node.f_cost:.1f}", True, (0, 0, 0)
                        )
                        self.screen.blit(cost_text, (x + 2, y + self.cell_size - 15))

    def _draw_ui(self):
        """Dessine l'interface utilisateur."""
        if not self.screen:
            return

        # Calculer position du panneau
        height, width = self.grid.shape if self.grid is not None else (15, 20)
        grid_width = width * self.cell_size
        panel_x = grid_width + 60
        panel_width = self.ui_panel_width - 20

        # Panneau principal
        panel_rect = pygame.Rect(panel_x, 20, panel_width, 500)
        pygame.draw.rect(self.screen, COLORS["ui_bg"], panel_rect)
        pygame.draw.rect(self.screen, COLORS["grid_line"], panel_rect, 2)

        # Titre
        title = self.font.render("Simulateur A*", True, COLORS["text"])
        self.screen.blit(title, (panel_x + 10, 30))

        y_offset = 60
        line_height = 20

        # État actuel
        state_text = f"État: {self.state.value}"
        state_surface = self.small_font.render(state_text, True, COLORS["text"])
        self.screen.blit(state_surface, (panel_x + 10, y_offset))
        y_offset += line_height + 10

        # Informations de la grille
        if self.grid is not None:
            grid_info = [
                f"Grille: {self.grid.shape[0]}x{self.grid.shape[1]}",
                f"Cellule: {self.edge_length:.1f}cm",
                f"Zoom: {self.cell_size}px",
            ]

            for info in grid_info:
                info_surface = self.small_font.render(info, True, COLORS["text"])
                self.screen.blit(info_surface, (panel_x + 10, y_offset))
                y_offset += line_height

        y_offset += 10

        # Points sélectionnés
        if self.visualizer:
            if self.visualizer.start_pos:
                start_text = f"🚀 Départ: {self.visualizer.start_pos}"
                start_surface = self.small_font.render(start_text, True, COLORS["text"])
                self.screen.blit(start_surface, (panel_x + 10, y_offset))
                y_offset += line_height

            if self.visualizer.goal_pos:
                goal_text = f"🎯 Arrivée: {self.visualizer.goal_pos}"
                goal_surface = self.small_font.render(goal_text, True, COLORS["text"])
                self.screen.blit(goal_surface, (panel_x + 10, y_offset))
                y_offset += line_height

        y_offset += 10

        # Statistiques A*
        if self.visualizer and self.visualizer.stats["iterations"] > 0:
            stats_title = self.font.render("Statistiques A*", True, COLORS["text"])
            self.screen.blit(stats_title, (panel_x + 10, y_offset))
            y_offset += 25

            stats_info = [
                f"Itérations: {self.visualizer.stats['iterations']}",
                f"Nœuds explorés: {self.visualizer.stats['nodes_explored']}",
                f"File d'attente: {self.visualizer.stats['nodes_in_queue']}",
                f"Longueur chemin: {self.visualizer.stats['path_length']}",
                f"Distance: {self.visualizer.stats['path_distance']:.2f}",
                f"Temps: {self.visualizer.stats['computation_time']:.2f}ms",
            ]

            for stat in stats_info:
                stat_surface = self.small_font.render(stat, True, COLORS["text"])
                self.screen.blit(stat_surface, (panel_x + 10, y_offset))
                y_offset += line_height

        y_offset += 20

        # Instructions
        instructions = [
            "Instructions:",
            "• Clic: Sélectionner points",
            "• ESPACE: Étape suivante",
            "• R: Reset",
            "• A: Auto/Manuel",
            "• +/-: Zoom",
            "• ESC: Quitter",
        ]

        for instruction in instructions:
            color = (
                COLORS["text"] if not instruction.startswith("•") else (100, 100, 100)
            )
            font = self.small_font if instruction.startswith("•") else self.font

            inst_surface = font.render(instruction, True, color)
            self.screen.blit(inst_surface, (panel_x + 10, y_offset))
            y_offset += line_height if instruction.startswith("•") else 25

    def _draw_buttons(self):
        """Dessine les boutons."""
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            button["hovered"] = button["rect"].collidepoint(mouse_pos)

            # Couleur du bouton
            if button["text"] == "Auto" and self.auto_step:
                color = COLORS["button_active"]
                text_color = (255, 255, 255)
            else:
                color = (
                    COLORS["button_hover"] if button["hovered"] else COLORS["button"]
                )
                text_color = COLORS["text"]

            # Dessiner bouton
            pygame.draw.rect(self.screen, color, button["rect"])
            pygame.draw.rect(self.screen, COLORS["grid_line"], button["rect"], 2)

            # Texte
            text_surface = self.small_font.render(button["text"], True, text_color)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            self.screen.blit(text_surface, text_rect)

    def _update_auto_step(self):
        """Mise à jour pour le mode automatique."""
        if (
            self.auto_step
            and self.state == SimulationState.RUNNING
            and pygame.time.get_ticks() - self.last_step_time > self.step_delay
        ):

            if self.visualizer.step():
                self.state = SimulationState.FINISHED
                self.auto_step = False
                print("🏁 Simulation automatique terminée")

            self.last_step_time = pygame.time.get_ticks()

    def run(self):
        """Boucle principale du simulateur."""
        clock = pygame.time.Clock()

        while self.running:
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        self._handle_click(event.pos)

                elif event.type == pygame.KEYDOWN:
                    self._handle_keyboard(event.key)

            # Mise à jour automatique
            self._update_auto_step()

            # Rendu
            self.screen.fill(COLORS["background"])
            self._draw_grid()
            self._draw_ui()
            self._draw_buttons()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def main():
    """Point d'entrée principal."""
    try:
        simulator = AStarSimulator()
        simulator.run()
    except Exception as e:
        print(f"Erreur fatale: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
