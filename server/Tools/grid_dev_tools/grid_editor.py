"""
Store Layout Grid Editor

Pygame interface to edit store grids used by the path optimization system.
Allows creating, modifying and saving layouts with free zones, obstacles and POIs.

Controls:
- Left click: Place free zone (0)
- Right click: Place obstacle (-1)
- Middle click: Place POI (1)
- S: Save
- R: Reset
- ESC: Quit without saving
- +/-: Adjust grid size
- Arrows: Move view
"""

import pygame
import numpy as np
import h5py
import sys
import os
from typing import Tuple, Optional, List
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import xxhash
import time

# Pathfinding imports
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from api_navimall.path_optimization.pathfinding_solver import (
        PathfindingSolver,
        PathfindingSolverFactory,
    )

    PATHFINDING_AVAILABLE = True
except ImportError as e:
    PATHFINDING_AVAILABLE = False
    print(f"⚠️ Pathfinding not available: {e}")

# Color configuration
COLORS = {
    "navigable": (255, 255, 255),  # White - free zone (0)
    "poi": (0, 255, 0),  # Green - point of interest (1)
    "obstacle": (0, 0, 0),  # Black - obstacle (-1)
    "grid_line": (128, 128, 128),  # Gray - grid lines
    "background": (200, 200, 200),  # Light gray - background
    "ui_bg": (240, 240, 240),  # Very light gray - interface
    "text": (0, 0, 0),  # Black - text
    "button": (180, 180, 180),  # Gray - buttons
    "button_hover": (160, 160, 160),  # Dark gray - hovered buttons
    # Pathfinding colors
    "path_start": (255, 0, 0),  # Red - starting point
    "path_goal": (0, 0, 255),  # Blue - goal point
    "path_line": (255, 165, 0),  # Orange - path
    "path_bg": (255, 255, 200),  # Light yellow - path background
}

# Default configuration
DEFAULT_GRID_SIZE = (20, 15)
DEFAULT_CELL_SIZE = 25
DEFAULT_EDGE_LENGTH = 100.0  # cm
MIN_CELL_SIZE = 10
MAX_CELL_SIZE = 50


class GridEditor:
    """Store grid editor with Pygame interface."""

    def __init__(self):
        """Initialize the grid editor."""
        pygame.init()

        # Display configuration
        self.cell_size = DEFAULT_CELL_SIZE
        self.grid_width, self.grid_height = DEFAULT_GRID_SIZE
        self.edge_length = DEFAULT_EDGE_LENGTH

        # User interface
        self.ui_panel_width = 350  # Info panel width
        self.ui_height = 120  # Button area height
        self.min_window_width = 800
        self.min_window_height = 600

        # Calculate window dimensions
        grid_display_width = self.grid_width * self.cell_size
        grid_display_height = self.grid_height * self.cell_size

        self.screen_width = max(
            self.min_window_width, grid_display_width + self.ui_panel_width + 100
        )
        self.screen_height = max(
            self.min_window_height, grid_display_height + self.ui_height + 100
        )

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Store Layout Grid Editor - NaviStore")

        # Fonts for text
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font = pygame.font.Font(None, 16)

        # Grid state
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
        self.original_grid = None
        self.has_changes = False

        # View offset
        self.offset_x = 50
        self.offset_y = 50

        # Interface state
        self.running = True
        self.current_tool = 0  # 0=navigable, -1=obstacle, 1=POI
        self.mouse_pressed = False

        # Mode coordonnées
        self.coordinate_mode = False
        self.last_clicked_cell = None
        self.last_clicked_coords = None

        # Mode pathfinding
        self.pathfinding_mode = False
        self.pathfinding_algorithm = "astar"
        self.path_start = None
        self.path_goal = None
        self.computed_path = None
        self.path_stats = None
        self.pathfinding_step = 0  # 0=choisir start, 1=choisir goal, 2=chemin calculé

        # Interface buttons
        self.buttons = self._create_buttons()

        # Statistics
        self.stats = {"navigable": 0, "obstacles": 0, "pois": 0}

        print("Store Layout Grid Editor initialized")
        print("Controls:")
        print("  Left click: Free zone (white)")
        print("  Right click: Obstacle (black)")
        print("  Middle click: POI (green)")
        print("  S: Save")
        print("  R: Reset")
        print("  ESC: Quit")
        print("  +/-: Adjust cell size")

    def _create_buttons(self) -> list:
        """Create interface buttons."""
        buttons = []
        y_pos = self.screen_height - 80

        button_configs = [
            ("Nouveau", self._new_grid, 50),
            ("Ouvrir", self._load_grid, 150),
            ("Sauver", self._save_grid, 250),
            ("Reset", self._reset_grid, 350),
            ("Taille", self._resize_grid, 450),
            ("Coord", self._toggle_coordinate_mode, 550),
            ("Path", self._toggle_pathfinding_mode, 650),
            ("Aide", self._show_help, 750),
            ("Quitter", self._quit_editor, 850),
        ]

        for text, callback, x_pos in button_configs:
            button = {
                "rect": pygame.Rect(x_pos, y_pos, 80, 30),
                "text": text,
                "callback": callback,
                "hovered": False,
            }
            buttons.append(button)

        return buttons

    def _update_stats(self):
        """Update grid statistics."""
        unique, counts = np.unique(self.grid, return_counts=True)
        stats_dict = dict(zip(unique, counts))

        self.stats = {
            "navigable": int(stats_dict.get(0, 0)),
            "obstacles": int(stats_dict.get(-1, 0)),
            "pois": int(stats_dict.get(1, 0)),
        }

    def _calculate_layout_hash(self) -> str:
        """Calculate XXH3 64-bit hash of the grid for a unique filename."""
        # Create data as in the optimization system
        grid_bytes = self.grid.astype(np.int8).tobytes()
        edge_length_bytes = np.array([self.edge_length], dtype=np.float64).tobytes()

        # Combine data
        combined_data = grid_bytes + edge_length_bytes

        # Calculer le hash XXH3 64-bit
        hasher = xxhash.xxh3_64()
        hasher.update(combined_data)

        return hasher.hexdigest()

    def _get_grid_pos(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Convert mouse position to grid coordinates (x=row, y=col)."""
        mx, my = mouse_pos

        # mx correspond aux colonnes (y), my correspond aux lignes (x)
        col = (mx - self.offset_x) // self.cell_size  # y coordinate
        row = (my - self.offset_y) // self.cell_size  # x coordinate

        if 0 <= col < self.grid_width and 0 <= row < self.grid_height:
            return int(row), int(col)  # Retourne (x=row, y=col)
        return None

    def _draw_grid(self):
        """Draw the main grid."""
        # Grid background
        grid_rect = pygame.Rect(
            self.offset_x,
            self.offset_y,
            self.grid_width * self.cell_size,
            self.grid_height * self.cell_size,
        )
        pygame.draw.rect(self.screen, COLORS["background"], grid_rect)

        # Draw cells
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cell_rect = pygame.Rect(
                    self.offset_x + x * self.cell_size,
                    self.offset_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )

                # Color according to cell type
                cell_value = self.grid[y, x]
                if cell_value == 0:
                    color = COLORS["navigable"]
                elif cell_value == 1:
                    color = COLORS["poi"]
                else:  # -1
                    color = COLORS["obstacle"]

                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, COLORS["grid_line"], cell_rect, 1)

        # Draw pathfinding elements if active
        if self.pathfinding_mode:
            self._draw_pathfinding_elements()

    def _draw_pathfinding_elements(self):
        """Draw pathfinding elements (start, goal, path)."""
        # Draw path first (under points)
        if self.computed_path and len(self.computed_path) > 1:
            # Convert path to screen coordinates
            path_points = []
            for px, py in self.computed_path:
                screen_x = self.offset_x + py * self.cell_size + self.cell_size // 2
                screen_y = self.offset_y + px * self.cell_size + self.cell_size // 2
                path_points.append((screen_x, screen_y))

            # Draw path lines
            if len(path_points) > 1:
                pygame.draw.lines(
                    self.screen, COLORS["path_line"], False, path_points, 3
                )

            # Draw points on path
            for point in path_points[1:-1]:  # Exclude start and goal
                pygame.draw.circle(self.screen, COLORS["path_line"], point, 2)

        # Draw starting point
        if self.path_start:
            start_x, start_y = self.path_start  # x=row, y=col
            start_rect = pygame.Rect(
                self.offset_x + start_y * self.cell_size + 2,
                self.offset_y + start_x * self.cell_size + 2,
                self.cell_size - 4,
                self.cell_size - 4,
            )
            pygame.draw.rect(self.screen, COLORS["path_start"], start_rect)
            pygame.draw.rect(self.screen, (128, 0, 0), start_rect, 2)

            # "S" label for Start
            if self.cell_size >= 20:
                font_size = min(self.cell_size - 8, 24)
                font = pygame.font.Font(None, font_size)
                text = font.render("S", True, (255, 255, 255))
                text_rect = text.get_rect(center=start_rect.center)
                self.screen.blit(text, text_rect)

        # Draw goal point
        if self.path_goal:
            goal_x, goal_y = self.path_goal  # x=row, y=col
            goal_rect = pygame.Rect(
                self.offset_x + goal_y * self.cell_size + 2,
                self.offset_y + goal_x * self.cell_size + 2,
                self.cell_size - 4,
                self.cell_size - 4,
            )
            pygame.draw.rect(self.screen, COLORS["path_goal"], goal_rect)
            pygame.draw.rect(self.screen, (0, 0, 128), goal_rect, 2)

            # "G" label for Goal
            if self.cell_size >= 20:
                font_size = min(self.cell_size - 8, 24)
                font = pygame.font.Font(None, font_size)
                text = font.render("G", True, (255, 255, 255))
                text_rect = text.get_rect(center=goal_rect.center)
                self.screen.blit(text, text_rect)

    def _draw_ui(self):
        """Draw the user interface."""
        # Calculate info panel position
        grid_display_width = self.grid_width * self.cell_size
        info_x = self.offset_x + grid_display_width + 20
        info_width = self.ui_panel_width
        info_height = min(self.screen_height - self.ui_height - 40, 600)

        # Main information panel
        info_rect = pygame.Rect(info_x, self.offset_y, info_width, info_height)
        pygame.draw.rect(self.screen, COLORS["ui_bg"], info_rect)
        pygame.draw.rect(self.screen, COLORS["grid_line"], info_rect, 2)

        # Title with version
        title_text = self.font.render(
            "Éditeur de Grille NaviStore", True, COLORS["text"]
        )
        self.screen.blit(title_text, (info_rect.x + 10, info_rect.y + 10))

        version_text = self.tiny_font.render(
            "v1.0 - JPS-TSP Editor", True, (100, 100, 100)
        )
        self.screen.blit(version_text, (info_rect.x + 10, info_rect.y + 35))

        y_offset = 55
        section_spacing = 25
        line_spacing = 18

        # Grid Information section
        self._draw_section_title(
            "Informations Grille", info_rect.x + 10, info_rect.y + y_offset
        )
        y_offset += section_spacing

        grid_info = [
            f"Dimensions: {self.grid_width} × {self.grid_height} cells",
            f"Cell size: {self.edge_length:.1f} cm",
            f"Total area: {(self.grid_width * self.edge_length / 100):.1f} × {(self.grid_height * self.edge_length / 100):.1f} m",
            f"Current zoom: {self.cell_size} pixels/cell",
        ]

        for text in grid_info:
            text_surface = self.small_font.render(text, True, COLORS["text"])
            self.screen.blit(text_surface, (info_rect.x + 15, info_rect.y + y_offset))
            y_offset += line_spacing

        y_offset += 10

        # Statistics section
        self._draw_section_title(
            "Statistiques", info_rect.x + 10, info_rect.y + y_offset
        )
        y_offset += section_spacing

        total_cells = self.grid_width * self.grid_height
        stats_info = [
            f"Total cellules: {total_cells}",
            f"Zones libres: {self.stats['navigable']} ({self.stats['navigable']/total_cells*100:.1f}%)",
            f"Obstacles: {self.stats['obstacles']} ({self.stats['obstacles']/total_cells*100:.1f}%)",
            f"Points d'intérêt: {self.stats['pois']} ({self.stats['pois']/total_cells*100:.1f}%)",
        ]

        for text in stats_info:
            text_surface = self.small_font.render(text, True, COLORS["text"])
            self.screen.blit(text_surface, (info_rect.x + 15, info_rect.y + y_offset))
            y_offset += line_spacing

        y_offset += 10

        # Tools section
        self._draw_section_title(
            "Outils de Dessin", info_rect.x + 10, info_rect.y + y_offset
        )
        y_offset += section_spacing

        tools_info = [
            "🖱️ Clic gauche: Zone libre (blanc)",
            "🖱️ Clic droit: Obstacle (noir)",
            "🖱️ Clic milieu: Point d'intérêt (vert)",
            "🖱️ Glisser: Dessiner en continu",
        ]

        for text in tools_info:
            text_surface = self.small_font.render(text, True, COLORS["text"])
            self.screen.blit(text_surface, (info_rect.x + 15, info_rect.y + y_offset))
            y_offset += line_spacing

        y_offset += 10

        # Keyboard shortcuts section
        self._draw_section_title(
            "Raccourcis Clavier", info_rect.x + 10, info_rect.y + y_offset
        )
        y_offset += section_spacing

        shortcuts_info = [
            "⌨️ S: Sauvegarder la grille",
            "⌨️ R: Réinitialiser/Reset",
            "⌨️ +/-: Ajuster le zoom",
            "⌨️ ESC: Quitter l'éditeur",
            "⌨️ Ctrl+N: Nouvelle grille",
            "⌨️ Ctrl+O: Ouvrir fichier",
        ]

        for text in shortcuts_info:
            text_surface = self.small_font.render(text, True, COLORS["text"])
            self.screen.blit(text_surface, (info_rect.x + 15, info_rect.y + y_offset))
            y_offset += line_spacing

        y_offset += 10

        # Color legend section
        self._draw_section_title("Légende", info_rect.x + 10, info_rect.y + y_offset)
        y_offset += section_spacing

        legend_items = [
            ("Zone libre (navigable)", COLORS["navigable"], "0"),
            ("Obstacle (mur/rayon)", COLORS["obstacle"], "-1"),
            ("Point d'intérêt", COLORS["poi"], "1"),
        ]

        for i, (label, color, value) in enumerate(legend_items):
            color_rect = pygame.Rect(info_rect.x + 15, y_offset + i * 22, 18, 18)
            pygame.draw.rect(self.screen, color, color_rect)
            pygame.draw.rect(self.screen, COLORS["grid_line"], color_rect, 1)

            label_text = self.small_font.render(
                f"{label} ({value})", True, COLORS["text"]
            )
            self.screen.blit(label_text, (info_rect.x + 40, y_offset + i * 22 + 2))

        y_offset += len(legend_items) * 22 + 15

        # Coordinates mode section
        coord_title_color = (0, 100, 200) if self.coordinate_mode else COLORS["text"]
        coord_title = (
            "🎯 Mode Coordonnées" if self.coordinate_mode else "Mode Coordonnées"
        )
        self._draw_section_title(
            coord_title, info_rect.x + 10, info_rect.y + y_offset, coord_title_color
        )
        y_offset += section_spacing

        if self.coordinate_mode:
            coord_info = [
                "🟢 ACTIF - Cliquez sur une case",
                "pour voir ses coordonnées",
            ]

            if self.last_clicked_cell:
                x, y = self.last_clicked_cell  # x=row, y=col
                world_x, world_y = self.last_clicked_coords
                cell_value = self.grid[x, y]

                value_names = {0: "libre", 1: "POI", -1: "obstacle"}
                value_name = value_names.get(cell_value, "inconnu")

                coord_info.extend(
                    [
                        "",
                        f"Dernière case cliquée:",
                        f"• Grille: ({x}, {y})",
                        f"• Monde: ({world_x:.1f}, {world_y:.1f}) cm",
                        f"• Type: {value_name} ({cell_value})",
                    ]
                )
        else:
            coord_info = [
                "🔘 INACTIF - Cliquez sur 'Coord'",
                "pour activer le mode",
            ]

        for text in coord_info:
            text_color = (0, 100, 200) if self.coordinate_mode else COLORS["text"]
            text_surface = self.small_font.render(text, True, text_color)
            self.screen.blit(text_surface, (info_rect.x + 15, info_rect.y + y_offset))
            y_offset += line_spacing

        y_offset += 15

        # Pathfinding mode section
        if PATHFINDING_AVAILABLE:
            path_title_color = (
                (200, 100, 0) if self.pathfinding_mode else COLORS["text"]
            )
            path_title = (
                "🎯 Mode Pathfinding" if self.pathfinding_mode else "Mode Pathfinding"
            )
            self._draw_section_title(
                path_title, info_rect.x + 10, info_rect.y + y_offset, path_title_color
            )
            y_offset += section_spacing

            if self.pathfinding_mode:
                path_info = [
                    f"🟢 ACTIF - Algorithme: {self.pathfinding_algorithm.upper()}",
                ]

                if self.pathfinding_step == 0:
                    path_info.append("1️⃣ Cliquez pour choisir le DÉPART")
                elif self.pathfinding_step == 1:
                    path_info.append("2️⃣ Cliquez pour choisir l'ARRIVÉE")
                    if self.path_start:
                        path_info.append(
                            f"   Départ: ({self.path_start[0]}, {self.path_start[1]})"
                        )
                elif self.pathfinding_step == 2:
                    path_info.append("3️⃣ Cliquez pour RECOMMENCER")

                # Afficher les statistiques si disponibles
                if self.path_stats:
                    path_info.append("")
                    if self.path_stats["success"]:
                        path_info.extend(
                            [
                                "✅ CHEMIN TROUVÉ:",
                                f"   Points: {self.path_stats['path_length']}",
                                f"   Distance: {self.path_stats['path_distance']:.2f}",
                                f"   Euclidienne: {self.path_stats['euclidean_distance']:.2f}",
                                f"   Ratio: {self.path_stats['efficiency_ratio']:.2f}",
                                f"   Temps: {self.path_stats['computation_time']:.1f}ms",
                            ]
                        )
                    else:
                        path_info.extend(
                            [
                                "❌ AUCUN CHEMIN:",
                                f"   Erreur: {self.path_stats.get('error', 'Inconnu')}",
                                f"   Distance eucl: {self.path_stats.get('euclidean_distance', 0):.2f}",
                            ]
                        )

                # Afficher les coordonnées des points sélectionnés
                if self.path_start:
                    path_info.append("")
                    path_info.append(
                        f"🚀 Départ: ({self.path_start[0]}, {self.path_start[1]})"
                    )
                if self.path_goal:
                    path_info.append(
                        f"🎯 Arrivée: ({self.path_goal[0]}, {self.path_goal[1]})"
                    )

            else:
                path_info = [
                    "🔘 INACTIF - Cliquez sur 'Path'",
                    "pour activer le test de chemins",
                    "",
                    "Fonctionnalités:",
                    "• Test de pathfinding A*",
                    "• Visualisation des chemins",
                    "• Statistiques détaillées",
                    "• Support obstacles/POIs",
                ]

            for text in path_info:
                text_color = (200, 100, 0) if self.pathfinding_mode else COLORS["text"]
                text_surface = self.small_font.render(text, True, text_color)
                self.screen.blit(
                    text_surface, (info_rect.x + 15, info_rect.y + y_offset)
                )
                y_offset += line_spacing
        else:
            # Pathfinding unavailable
            self._draw_section_title(
                "❌ Pathfinding indisponible",
                info_rect.x + 10,
                info_rect.y + y_offset,
                (150, 150, 150),
            )
            y_offset += section_spacing

            unavailable_info = [
                "Module pathfinding manquant",
                "Installez avec:",
                "pip install pathfinding",
            ]

            for text in unavailable_info:
                text_surface = self.small_font.render(text, True, (150, 150, 150))
                self.screen.blit(
                    text_surface, (info_rect.x + 15, info_rect.y + y_offset)
                )
                y_offset += line_spacing

        # Unsaved changes indicator at top
        if self.has_changes:
            changes_text = self.font.render(
                "⚠️ Modifications non sauvées", True, (255, 0, 0)
            )
            self.screen.blit(changes_text, (10, 10))
        else:
            saved_text = self.small_font.render("✅ Sauvegardé", True, (0, 150, 0))
            self.screen.blit(saved_text, (10, 15))

    def _draw_section_title(self, title: str, x: int, y: int, color=None):
        """Draw a section title."""
        if color is None:
            color = COLORS["text"]

        # Colored background for title
        title_surface = self.font.render(title, True, color)
        title_rect = pygame.Rect(
            x - 5, y - 2, title_surface.get_width() + 10, title_surface.get_height() + 4
        )
        pygame.draw.rect(self.screen, (220, 220, 220), title_rect)
        pygame.draw.rect(self.screen, COLORS["grid_line"], title_rect, 1)
        self.screen.blit(title_surface, (x, y))

    def _draw_buttons(self):
        """Draw interface buttons."""
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            # Check hover
            button["hovered"] = button["rect"].collidepoint(mouse_pos)

            # Special color for active buttons
            if button["text"] == "Coord" and self.coordinate_mode:
                color = (100, 150, 255)  # Blue for active mode
                text_color = (255, 255, 255)  # White text
            elif button["text"] == "Path" and self.pathfinding_mode:
                color = (255, 150, 50)  # Orange for active pathfinding mode
                text_color = (255, 255, 255)  # White text
            elif button["text"] == "Path" and not PATHFINDING_AVAILABLE:
                color = (120, 120, 120)  # Gray for unavailable pathfinding
                text_color = (200, 200, 200)  # Light gray text
            else:
                color = (
                    COLORS["button_hover"] if button["hovered"] else COLORS["button"]
                )
                text_color = COLORS["text"]

            # Draw button
            pygame.draw.rect(self.screen, color, button["rect"])
            pygame.draw.rect(self.screen, COLORS["grid_line"], button["rect"], 2)

            # Button text
            text_surface = self.small_font.render(button["text"], True, text_color)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            self.screen.blit(text_surface, text_rect)

    def _handle_mouse_click(self, pos: Tuple[int, int], button: int):
        """Handle mouse clicks."""
        # Check button clicks
        for ui_button in self.buttons:
            if ui_button["rect"].collidepoint(pos):
                ui_button["callback"]()
                return

        # Get position in grid
        grid_pos = self._get_grid_pos(pos)
        if grid_pos:
            x, y = grid_pos  # x=row, y=col

            # Pathfinding mode: start/goal point management
            if self.pathfinding_mode and button == 1:  # Left click only
                # Check that cell is free
                if self.grid[x, y] == -1:  # Obstacle
                    print(f"❌ Cannot select obstacle at ({x}, {y})")
                    return

                if self.pathfinding_step == 0:  # Choose start
                    self.path_start = (x, y)
                    self.pathfinding_step = 1
                    print(
                        f"🚀 Point de départ sélectionné: ({x}, {y}) - Cliquez pour choisir l'arrivée"
                    )

                elif self.pathfinding_step == 1:  # Choose goal
                    if (x, y) == self.path_start:
                        print("⚠️ Goal point must be different from starting point")
                        return

                    self.path_goal = (x, y)
                    print(f"🎯 Goal point selected: ({x}, {y}) - Computing path...")

                    # Calculate path automatically
                    self._compute_pathfinding()

                elif self.pathfinding_step == 2:  # Path calculated, restart
                    print("🔄 New test - Click to choose starting point")
                    self._reset_pathfinding()
                    self.path_start = (x, y)
                    self.pathfinding_step = 1
                    print(
                        f"🚀 Starting point selected: ({x}, {y}) - Click to choose destination"
                    )

                return

            # Coordinates mode: display information
            if self.coordinate_mode:
                world_x, world_y = self._calculate_world_coordinates(x, y)
                self.last_clicked_cell = (x, y)
                self.last_clicked_coords = (world_x, world_y)

                # Display in console
                print(f"🎯 Cell coordinates:")
                print(f"   Grid: (x={x}, y={y}) = (row={x}, col={y})")
                print(f"   World: ({world_x:.1f}cm, {world_y:.1f}cm)")
                print(f"   Value: {self.grid[x, y]}")
                return

            # Normal edit mode (if not pathfinding nor coordinates)
            if not self.pathfinding_mode and not self.coordinate_mode:
                # Determine value by button
                if button == 1:  # Left click - free zone
                    new_value = 0
                elif button == 3:  # Right click - obstacle
                    new_value = -1
                elif button == 2:  # Middle click - POI
                    new_value = 1
                else:
                    return

                # Apply modification
                if self.grid[x, y] != new_value:  # grid[row, col]
                    self.grid[x, y] = new_value
                    self.has_changes = True
                    self._update_stats()

    def _handle_mouse_drag(self, pos: Tuple[int, int]):
        """Handle mouse dragging."""
        if self.mouse_pressed:
            grid_pos = self._get_grid_pos(pos)
            if grid_pos:
                x, y = grid_pos  # x=row, y=col selon nouvelle convention

                # Use current tool
                if self.grid[x, y] != self.current_tool:
                    self.grid[x, y] = self.current_tool
                    self.has_changes = True
                    self._update_stats()

    def _new_grid(self):
        """Create a new grid."""
        if self.has_changes:
            if not self._confirm_action(
                "Créer une nouvelle grille? Les modifications non sauvées seront perdues."
            ):
                return

        # Ask for dimensions
        root = tk.Tk()
        root.withdraw()

        try:
            width = simpledialog.askinteger(
                "Nouvelle grille",
                "Largeur:",
                initialvalue=self.grid_width,
                minvalue=5,
                maxvalue=100,
            )
            if width is None:
                return

            height = simpledialog.askinteger(
                "Nouvelle grille",
                "Hauteur:",
                initialvalue=self.grid_height,
                minvalue=5,
                maxvalue=100,
            )
            if height is None:
                return

            edge_length = simpledialog.askfloat(
                "Nouvelle grille",
                "Taille cellule (cm):",
                initialvalue=self.edge_length,
                minvalue=10.0,
                maxvalue=500.0,
            )
            if edge_length is None:
                return

            # Créer nouvelle grille
            self.grid_width, self.grid_height = width, height
            self.edge_length = edge_length
            self.grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
            self.original_grid = None
            self.has_changes = False
            self._update_stats()

            # Ajuster la fenêtre
            self._adjust_window_size()

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création: {str(e)}")
        finally:
            root.destroy()

    def _load_grid(self):
        """Load grid from HDF5 file."""
        if self.has_changes:
            if not self._confirm_action(
                "Charger une grille? Les modifications non sauvées seront perdues."
            ):
                return

        root = tk.Tk()
        root.withdraw()

        try:
            file_path = filedialog.askopenfilename(
                title="Charger grille",
                filetypes=[("Fichiers HDF5", "*.h5"), ("Tous fichiers", "*.*")],
                initialdir=os.path.join(
                    os.path.dirname(__file__), "..", "assets", "layouts"
                ),
            )

            if file_path:
                with h5py.File(file_path, "r") as f:
                    layout = np.array(f["layout"])
                    edge_length = float(f["edge_length"][()])

                    # Get stored hash if it exists
                    stored_hash = f.attrs.get("layout_hash", "Non disponible")

                self.grid = layout
                self.grid_height, self.grid_width = layout.shape
                self.edge_length = edge_length
                self.original_grid = layout.copy()
                self.has_changes = False
                self._update_stats()

                # Calculate current hash for verification
                current_hash = self._calculate_layout_hash()

                # Check integrity
                hash_match = (
                    stored_hash != "Non disponible" and stored_hash == current_hash
                )

                # Extract filename for display
                filename = os.path.basename(file_path)

                # Ajuster la fenêtre
                self._adjust_window_size()

                # Success message with detailed information
                info_message = f"Grille chargée: {self.grid_width}x{self.grid_height}\n"
                info_message += f"Fichier: {filename}\n"
                info_message += f"Hash XXH3: {current_hash}\n"

                if stored_hash != "Non disponible":
                    if hash_match:
                        info_message += "✓ Intégrité vérifiée"
                    else:
                        info_message += f"⚠ Hash différent du stocké: {stored_hash}"
                else:
                    info_message += "ℹ Pas de hash stocké (fichier ancien)"

                messagebox.showinfo("Succès", info_message)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            root.destroy()

    def _save_grid(self):
        """Save current grid with XXH3 64-bit hash as filename."""
        root = tk.Tk()
        root.withdraw()

        try:
            # Calculate XXH3 64-bit hash of grid
            layout_hash = self._calculate_layout_hash()

            # Propose save directory
            save_dir = filedialog.askdirectory(
                title="Choisir le répertoire de sauvegarde",
                initialdir=os.path.join(
                    os.path.dirname(__file__), "..", "assets", "layouts"
                ),
            )

            if save_dir:
                # Create filename based on hash
                file_path = os.path.join(save_dir, f"{layout_hash}.h5")

                # Check if file already exists
                if os.path.exists(file_path):
                    if not messagebox.askyesno(
                        "Fichier existant",
                        f"Le fichier {layout_hash}.h5 existe déjà.\n"
                        "Voulez-vous l'écraser?",
                    ):
                        return

                with h5py.File(file_path, "w") as f:
                    f.create_dataset("layout", data=self.grid)
                    f.create_dataset("edge_length", data=self.edge_length)

                    # Add hash as attribute for verification
                    f.attrs["layout_hash"] = layout_hash
                    f.attrs["created_with"] = "NaviStore Grid Editor"

                self.original_grid = self.grid.copy()
                self.has_changes = False

                # Also save metadata with same name
                metadata_file = os.path.join(save_dir, f"{layout_hash}_metadata.json")

                # Convert NumPy types to native Python types for JSON
                def convert_numpy_types(obj):
                    """Convertit les types NumPy en types Python natifs."""
                    if isinstance(obj, np.integer):
                        return int(obj)
                    elif isinstance(obj, np.floating):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif isinstance(obj, tuple):
                        return tuple(convert_numpy_types(item) for item in obj)
                    elif isinstance(obj, dict):
                        return {
                            key: convert_numpy_types(value)
                            for key, value in obj.items()
                        }
                    elif isinstance(obj, list):
                        return [convert_numpy_types(item) for item in obj]
                    return obj

                metadata = {
                    "layout_hash": layout_hash,
                    "grid_shape": [int(self.grid.shape[0]), int(self.grid.shape[1])],
                    "edge_length": float(self.edge_length),
                    "statistics": convert_numpy_types(self.stats),
                    "file_path": file_path,
                    "created_with": "NaviStore Grid Editor",
                }

                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                messagebox.showinfo(
                    "Succès",
                    f"Grille sauvegardée:\n"
                    f"Nom: {layout_hash}.h5\n"
                    f"Hash XXH3: {layout_hash}\n"
                    f"Chemin: {file_path}",
                )

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
        finally:
            root.destroy()

    def _reset_grid(self):
        """Reset grid to original state."""
        if self.original_grid is not None:
            if self._confirm_action("Annuler toutes les modifications?"):
                self.grid = self.original_grid.copy()
                self.has_changes = False
                self._update_stats()
        else:
            if self._confirm_action("Effacer toute la grille?"):
                self.grid.fill(0)
                self.has_changes = True
                self._update_stats()

    def _resize_grid(self):
        """Resize the grid."""
        root = tk.Tk()
        root.withdraw()

        try:
            width = simpledialog.askinteger(
                "Redimensionner",
                "Nouvelle largeur:",
                initialvalue=self.grid_width,
                minvalue=5,
                maxvalue=100,
            )
            if width is None:
                return

            height = simpledialog.askinteger(
                "Redimensionner",
                "Nouvelle hauteur:",
                initialvalue=self.grid_height,
                minvalue=5,
                maxvalue=100,
            )
            if height is None:
                return

            # Create new grid with resizing
            new_grid = np.zeros((height, width), dtype=int)

            # Copy old grid (truncate or extend as needed)
            copy_height = min(self.grid_height, height)
            copy_width = min(self.grid_width, width)

            new_grid[:copy_height, :copy_width] = self.grid[:copy_height, :copy_width]

            self.grid = new_grid
            self.grid_width, self.grid_height = width, height
            self.has_changes = True
            self._update_stats()

            # Ajuster la fenêtre
            self._adjust_window_size()

        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Erreur lors du redimensionnement: {str(e)}"
            )
        finally:
            root.destroy()

    def _adjust_window_size(self):
        """Adjust window size according to grid."""
        # Calculate new dimensions
        grid_display_width = self.grid_width * self.cell_size
        grid_display_height = self.grid_height * self.cell_size

        new_width = max(
            self.min_window_width, grid_display_width + self.ui_panel_width + 100
        )
        new_height = max(
            self.min_window_height, grid_display_height + self.ui_height + 100
        )

        self.screen_width = new_width
        self.screen_height = new_height
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )

        # Recreate buttons with new positions
        self.buttons = self._create_buttons()

        # Update statistics
        self._update_stats()

    def _confirm_action(self, message: str) -> bool:
        """Display confirmation dialog."""
        root = tk.Tk()
        root.withdraw()
        try:
            result = messagebox.askyesno("Confirmation", message)
            return result
        finally:
            root.destroy()

    def _toggle_pathfinding_mode(self):
        """Enable/disable pathfinding mode."""
        if not PATHFINDING_AVAILABLE:
            messagebox.showerror(
                "Pathfinding indisponible",
                "Le module pathfinding n'est pas disponible.\nInstallez avec: pip install pathfinding",
            )
            return

        self.pathfinding_mode = not self.pathfinding_mode

        if self.pathfinding_mode:
            # Disable coordinates mode if active
            self.coordinate_mode = False
            # Reset pathfinding state
            self._reset_pathfinding()
            print("🎯 Pathfinding mode enabled - Click to choose starting point")
        else:
            self._reset_pathfinding()
            print("🔘 Pathfinding mode disabled")

    def _reset_pathfinding(self):
        """Reset pathfinding state to zero."""
        self.path_start = None
        self.path_goal = None
        self.computed_path = None
        self.path_stats = None
        self.pathfinding_step = 0

    def _compute_pathfinding(self):
        """Calculate path between start and goal."""
        if not self.path_start or not self.path_goal:
            return

        try:
            # Create solver
            poi_coords = np.array([self.path_start, self.path_goal])

            solver = PathfindingSolverFactory.create_solver(
                grid_with_poi=self.grid,
                distance_threshold_grid=1000000.0,  # Seuil très élevé
                poi_coords=poi_coords,
                algorithm=self.pathfinding_algorithm,
                diagonal_movement=True,
            )

            # Calculate path
            start_time = time.time()
            path = solver.find_path(self.path_start, self.path_goal)
            computation_time = time.time() - start_time

            # Calculate statistics
            euclidean_dist = np.sqrt(
                (self.path_goal[0] - self.path_start[0]) ** 2
                + (self.path_goal[1] - self.path_start[1]) ** 2
            )

            if path:
                path_distance = 0.0
                if len(path) > 1:
                    for i in range(len(path) - 1):
                        p1, p2 = path[i], path[i + 1]
                        path_distance += np.sqrt(
                            (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2
                        )

                self.path_stats = {
                    "success": True,
                    "algorithm": self.pathfinding_algorithm.upper(),
                    "computation_time": computation_time * 1000,  # en ms
                    "path_length": len(path),
                    "euclidean_distance": euclidean_dist,
                    "path_distance": path_distance,
                    "efficiency_ratio": (
                        path_distance / euclidean_dist if euclidean_dist > 0 else 0
                    ),
                }

                print(
                    f"✅ Path found: {len(path)} points, distance: {path_distance:.2f}"
                )
            else:
                self.path_stats = {
                    "success": False,
                    "algorithm": self.pathfinding_algorithm.upper(),
                    "computation_time": computation_time * 1000,
                    "euclidean_distance": euclidean_dist,
                    "error": "No path found",
                }
                print("❌ No path found")

            self.computed_path = path
            self.pathfinding_step = 2

        except Exception as e:
            self.path_stats = {
                "success": False,
                "error": str(e),
                "algorithm": self.pathfinding_algorithm.upper(),
            }
            print(f"❌ Pathfinding error: {e}")

    def _toggle_coordinate_mode(self):
        """Enable/disable coordinates mode."""
        self.coordinate_mode = not self.coordinate_mode
        if self.coordinate_mode:
            self.last_clicked_cell = None
            self.last_clicked_coords = None

    def _calculate_world_coordinates(
        self, grid_x: int, grid_y: int
    ) -> Tuple[float, float]:
        """Calculate world coordinates (cell center) from grid indices.
        Args:
            grid_x: row (line)
            grid_y: col (column)
        Returns:
            (world_x, world_y) where world_x corresponds to grid_x and world_y to grid_y
        """
        # Cell center coordinates in centimeters
        # grid_x (row) -> world_x, grid_y (col) -> world_y
        world_x = (grid_x + 0.5) * self.edge_length
        world_y = (grid_y + 0.5) * self.edge_length
        return world_x, world_y

    def _show_help(self):
        """Display editor help."""
        help_text = """HELP - GRID EDITOR

    DRAWING TOOLS:
    • Left click: Place navigable zone (white)
    • Right click: Place obstacles (black)
    • Middle click: Place POI (red)

    KEYBOARD CONTROLS:
    • S: Save
    • R: Reset grid
    • ESC: Quit
    • +/-: Adjust cell size
    • Arrows: Move view

    BUTTONS:
    • New: Create new grid
    • Open: Load existing grid
    • Save: Save current grid
    • Reset: Clear the grid
    • Size: Resize grid
    • Coord: Coordinates mode (display)
    • Help: Show this help
    • Quit: Close editor

    COORDINATES MODE:
    • Activate with 'Coord' button
    • Click on a cell to see:
      - Grid position (x, y)
      - World coordinates (cm)
      - Cell type
    • Temporarily disables editing

    LEGEND:
    • White: Navigable zone (value 0)
    • Black: Obstacle (value -1)
    • Red: Point of interest/POI (value 1)

    SAVE FORMAT:
    • Files named with XXH3 64-bit hash
    • HDF5 format with metadata
    • Compatible with optimization system
    • Automatic integrity check

    EXAMPLE: a1b2c3d4e5f6.h5
    The name corresponds to content's XXH3 hash."""

        self._show_info_dialog(help_text, "Aide")

    def _quit_editor(self):
        """Quit the editor."""
        if self.has_changes:
            if not self._confirm_action("Quitter sans sauvegarder les modifications?"):
                return
        self.running = False

    def _handle_keyboard(self, key):
        """Handle keyboard input."""
        keys = pygame.key.get_pressed()
        ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        if key == pygame.K_s:
            self._save_grid()
        elif key == pygame.K_r:
            self._reset_grid()
        elif key == pygame.K_ESCAPE:
            self._quit_editor()
        elif key == pygame.K_n and ctrl_pressed:
            self._new_grid()
        elif key == pygame.K_o and ctrl_pressed:
            self._load_grid()
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            if self.cell_size < MAX_CELL_SIZE:
                self.cell_size += 2
                self._adjust_window_size()
        elif key == pygame.K_MINUS:
            if self.cell_size > MIN_CELL_SIZE:
                self.cell_size -= 2
                self._adjust_window_size()
        elif key == pygame.K_F1:
            self._show_help()
        elif key == pygame.K_p:
            self._toggle_pathfinding_mode()
        elif key == pygame.K_c:
            self._toggle_coordinate_mode()
        elif key == pygame.K_SPACE and self.pathfinding_mode:
            # Spacebar to restart pathfinding
            self._reset_pathfinding()

    def _show_help(self):
        """Display help."""
        root = tk.Tk()
        root.withdraw()

        help_text = """
    NaviStore Grid Editor - Help

    DRAWING TOOLS:
    • Left click: Free zone (navigable) - value 0
    • Right click: Obstacle (wall, shelf) - value -1  
    • Middle click: Point of interest (POI) - value 1
    • Drag: Draw continuously

    KEYBOARD SHORTCUTS:
    • S: Save grid
    • R: Reset
    • ESC: Quit editor 
    • Ctrl+N: New grid
    • Ctrl+O: Open file
    • +/-: Adjust zoom
    • F1: Show this help
    • P: Enable/disable pathfinding mode
    • C: Enable/disable coordinate mode
    • SPACE: Reset pathfinding (if mode active)

    BUTTONS:
    • New: Create grid (custom dimensions)
    • Open: Load from .h5 file 
    • Save: Save to .h5 format
    • Reset: Cancel modifications
    • Size: Resize grid
    • Coord: Coordinate mode (display info)
    • Path: Pathfinding mode (test paths)
    • Quit: Close editor

    PATHFINDING MODE:
    • Enable with 'Path' button or 'P' key
    • 1. Click free cell for start point
    • 2. Click free cell for goal point 
    • 3. Path displays automatically
    • Statistics: length, distance, computation time
    • Visualization: orange line, red/blue points
    • Click anywhere to restart

    TIPS:
    • Use 1-2 cell wide aisles
    • Keep real store proportions
    • Test navigation between all POIs
    • Pathfinding helps validate connectivity
    • Save your work regularly
        """

        try:
            messagebox.showinfo("Aide - Éditeur de Grille", help_text)
        finally:
            root.destroy()

    def run(self):
        """Main editor loop."""
        clock = pygame.time.Clock()

        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit_editor()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in [1, 2, 3]:  # Left, middle, right
                        self._handle_mouse_click(event.pos, event.button)
                        self.mouse_pressed = True

                        # Set current tool for dragging
                        if event.button == 1:
                            self.current_tool = 0
                        elif event.button == 3:
                            self.current_tool = -1
                        elif event.button == 2:
                            self.current_tool = 1

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse_pressed = False

                elif event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_drag(event.pos)

                elif event.type == pygame.KEYDOWN:
                    self._handle_keyboard(event.key)

                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resizing
                    self.screen_width = max(self.min_window_width, event.w)
                    self.screen_height = max(self.min_window_height, event.h)
                    self.screen = pygame.display.set_mode(
                        (self.screen_width, self.screen_height), pygame.RESIZABLE
                    )
                    self.buttons = self._create_buttons()

            # Rendering
            self.screen.fill(COLORS["background"])
            self._draw_grid()
            self._draw_ui()
            self._draw_buttons()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def main():
    """Main entry point."""
    try:
        editor = GridEditor()
        editor.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
