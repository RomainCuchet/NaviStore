"""
Refactored Store Layout Grid Editor
- Menu bar (File, Mode) with dropdowns
- 'Infos' panel grouped and toggleable from File menu
- Side color/type palette (black, green, orange) that controls right-click placement while pressed
- Mode selection (Coord / Path) in Mode menu; only active mode shows its information in a dedicated area under the main grid
- Removed the old large button toolbar: file actions moved into File menu
- Maintains original functionality (load/save/new/reset/resize/pathfinding/coord) using the same dialog functions

Notes:
- This is still a single-file implementation for clarity, but UI drawing and application logic have been separated into distinct methods
- The Pygame-based "menu bar" is custom-drawn (there is no native OS menu integration)

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

# Pathfinding imports (kept as before)
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from api_navimall.path_optimization.pathfinding_solver import (
        PathfindingSolver,
        PathfindingSolverFactory,
    )
    from api_navimall.path_optimization.utils import (
        load_layout_from_h5,
        save_layout_to_h5,
        Zone,
    )

    PATHFINDING_AVAILABLE = True
except ImportError as e:
    PATHFINDING_AVAILABLE = False
    print(f"⚠️ Pathfinding not available: {e}")

# Color configuration -- re-used
COLORS = {
    "navigable": (255, 255, 255),  # White - free zone (0)
    "poi": (0, 255, 0),  # Green - point of interest (1)
    "obstacle": (0, 0, 0),  # Black - obstacle (-1)
    "shelf": (255, 165, 0),  # Orange-ish for shelf to match palette (2)
    "zone": (255, 255, 0, 80),  # Semi-transparent yellow - zones
    "grid_line": (128, 128, 128),  # Gray - grid lines
    "background": (200, 200, 200),  # Light gray - background
    "ui_bg": (245, 245, 245),  # Very light gray - interface
    "text": (10, 10, 10),  # Dark text
    "button": (220, 220, 220),
    "button_hover": (200, 200, 200),
    "menu_bg": (230, 230, 230),
    "menu_hover": (200, 220, 255),
    # Pathfinding colors
    "path_start": (255, 0, 0),
    "path_goal": (0, 0, 255),
    "path_line": (255, 165, 0),
}

# Defaults
DEFAULT_GRID_SIZE = (20, 15)
DEFAULT_CELL_SIZE = 25
DEFAULT_EDGE_LENGTH = 100.0  # cm
MIN_CELL_SIZE = 10
MAX_CELL_SIZE = 50


class GridEditor:
    """Refactored Grid Editor with menu bar and side palette."""

    def __init__(self):
        pygame.init()

        # Display configuration
        self.cell_size = DEFAULT_CELL_SIZE
        self.grid_width, self.grid_height = DEFAULT_GRID_SIZE
        self.edge_length = DEFAULT_EDGE_LENGTH

        # UI sizes
        self.ui_panel_width = 350
        self.mode_info_height = (
            120  # area under main grid reserved for mode-specific info
        )
        self.top_menu_height = 28
        self.min_window_width = 900
        self.min_window_height = 650

        # Compute sizes
        grid_display_width = self.grid_width * self.cell_size
        grid_display_height = self.grid_height * self.cell_size

        self.screen_width = max(
            self.min_window_width, grid_display_width + self.ui_panel_width + 200
        )
        self.screen_height = max(
            self.min_window_height,
            grid_display_height + self.mode_info_height + 200,
        )

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )
        pygame.display.set_caption("NaviStore Grid Editor — Modern UI")

        # Fonts
        self.font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font = pygame.font.Font(None, 14)

        # Model (grid state)
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
        self.original_grid = None
        self.has_changes = False
        self.zones = []

        # View offsets
        self.offset_x = 100
        self.offset_y = self.top_menu_height + 20

        # Interaction state
        self.running = True
        self.current_tool = 0  # left-click tool (0, -1, 1, 2)
        self.side_selected_tool = -1  # set by side palette (black/-1 default)

        # Dragging state: which tool is currently being applied while mouse held
        self.drag_tool: Optional[int] = None

        # Modes
        self.coordinate_mode = False
        self.pathfinding_mode = False
        self.pathfinding_algorithm = "astar"
        self.path_start = None
        self.path_goal = None
        self.computed_path = None
        self.path_stats = None
        self.pathfinding_step = 0

        # Stats
        self.stats = {"navigable": 0, "obstacles": 0, "pois": 0, "shelves": 0}

        # Menu state
        self.menu_items = ["Fichier", "Mode", "Aide"]
        self.open_dropdown = None  # None or one of menu names
        self.infos_visible = True  # grouped "Infos" panel visibility

        # Dropdown definitions: each is list of (label, callback, shortcut)
        self.dropdowns = {
            "Fichier": [
                ("Nouveau \t Ctrl+N", self._new_grid, (pygame.K_n, True)),
                ("Ouvrir \t Ctrl+O", self._load_grid, (pygame.K_o, True)),
                ("Sauver \t Ctrl+S", self._save_grid, (pygame.K_s, True)),
                ("Reset", self._reset_grid, None),
                ("Taille...", self._resize_grid, None),
                ("—", None, None),
                ("Infos (afficher/masquer)", self._toggle_infos, None),
                ("Aide", self._show_help, None),
                ("Quitter \t Ctrl+Q", self._quit_editor, (pygame.K_q, True)),
            ],
            "Mode": [
                ("Coordonnées", self._activate_coordinate_mode, None),
                ("Pathfinding", self._activate_pathfinding_mode, None),
            ],
            "Aide": [
                ("À propos", self._show_about, None),
            ],
        }

        # Palette on left side (black, green, orange)
        # Each palette item is (label, color, value)
        self.palette = [
            ("Obstacle", COLORS["obstacle"], -1),  # black
            ("POI", COLORS["poi"], 1),  # green
            ("Étagère", COLORS["shelf"], 2),  # orange
        ]

        # Remove legacy big buttons; file actions are now in menu
        self.buttons = []

        # Misc prints
        print("NaviStore Grid Editor (refactored) initialized")

        # Initial stats
        self._update_stats()

    # ------------------------- Model utilities -------------------------
    def _update_stats(self):
        unique, counts = np.unique(self.grid, return_counts=True)
        stats_dict = dict(zip(unique, counts))
        self.stats = {
            "navigable": int(stats_dict.get(0, 0)),
            "obstacles": int(stats_dict.get(-1, 0)),
            "pois": int(stats_dict.get(1, 0)),
            "shelves": int(stats_dict.get(2, 0)),
        }

    def _calculate_layout_hash(self) -> str:
        grid_bytes = self.grid.astype(np.int8).tobytes()
        edge_length_bytes = np.array([self.edge_length], dtype=np.float64).tobytes()
        combined_data = grid_bytes + edge_length_bytes
        hasher = xxhash.xxh3_64()
        hasher.update(combined_data)
        return hasher.hexdigest()

    def _calculate_world_coordinates(
        self, grid_x: int, grid_y: int
    ) -> Tuple[float, float]:
        world_x = (grid_x + 0.5) * self.edge_length
        world_y = (grid_y + 0.5) * self.edge_length
        return world_x, world_y

    # ------------------------- File operations (unchanged logic) -------------------------
    def _new_grid(self):
        if self.has_changes:
            if not self._confirm_action(
                "Créer une nouvelle grille? Les modifications non sauvées seront perdues."
            ):
                return

        root = tk.Tk()
        root.withdraw()
        try:
            width = simpledialog.askinteger(
                "Nouvelle grille",
                "Largeur:",
                initialvalue=self.grid_width,
                minvalue=5,
                maxvalue=200,
            )
            if width is None:
                return
            height = simpledialog.askinteger(
                "Nouvelle grille",
                "Hauteur:",
                initialvalue=self.grid_height,
                minvalue=5,
                maxvalue=200,
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
            self.grid_width, self.grid_height = width, height
            self.edge_length = edge_length
            self.grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
            self.original_grid = None
            self.has_changes = False
            self._adjust_window_size()
            self._update_stats()
        finally:
            root.destroy()

    def _load_grid(self):
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
            )
            if not file_path:
                return
            if PATHFINDING_AVAILABLE:
                layout, edge_length, zones_dict = load_layout_from_h5(file_path)
                self.zones = list(zones_dict.values())
            else:
                with h5py.File(file_path, "r") as f:
                    layout = np.array(f["layout"])
                    edge_length = float(f["edge_length"][()])
                self.zones = []
            with h5py.File(file_path, "r") as f:
                stored_hash = f.attrs.get("layout_hash", "Non disponible")
            self.grid = layout
            self.grid_height, self.grid_width = layout.shape
            self.edge_length = edge_length
            self.original_grid = layout.copy()
            self.has_changes = False
            self._update_stats()
            current_hash = self._calculate_layout_hash()
            filename = os.path.basename(file_path)
            info_message = f"Grille chargée: {self.grid_width}x{self.grid_height}\nFichier: {filename}\nHash XXH3: {current_hash}\n"
            if stored_hash != "Non disponible":
                if stored_hash == current_hash:
                    info_message += "✓ Intégrité vérifiée"
                else:
                    info_message += f"⚠ Hash différent du stocké: {stored_hash}"
            else:
                info_message += "ℹ Pas de hash stocké (fichier ancien)"
            messagebox.showinfo("Succès", info_message)
            self._adjust_window_size()
        finally:
            root.destroy()

    def _save_grid(self):
        root = tk.Tk()
        root.withdraw()
        try:
            layout_hash = self._calculate_layout_hash()
            save_dir = filedialog.askdirectory(
                title="Choisir le répertoire de sauvegarde"
            )
            if not save_dir:
                return
            file_path = os.path.join(save_dir, f"{layout_hash}.h5")
            if os.path.exists(file_path):
                if not messagebox.askyesno(
                    "Fichier existant",
                    f"Le fichier {layout_hash}.h5 existe déjà.\nVoulez-vous l'écraser?",
                ):
                    return
            if PATHFINDING_AVAILABLE:
                zones_dict = {f"zone_{i}": zone for i, zone in enumerate(self.zones)}
                save_layout_to_h5(file_path, self.grid, self.edge_length, zones_dict)
                with h5py.File(file_path, "a") as f:
                    f.attrs["layout_hash"] = layout_hash
                    f.attrs["created_with"] = "NaviStore Grid Editor"
            else:
                with h5py.File(file_path, "w") as f:
                    f.create_dataset("layout", data=self.grid)
                    f.create_dataset("edge_length", data=self.edge_length)
                    f.attrs["layout_hash"] = layout_hash
                    f.attrs["created_with"] = "NaviStore Grid Editor"
            self.original_grid = self.grid.copy()
            self.has_changes = False
            # metadata
            metadata_file = os.path.join(save_dir, f"{layout_hash}_metadata.json")
            metadata = {
                "layout_hash": layout_hash,
                "grid_shape": [int(self.grid.shape[0]), int(self.grid.shape[1])],
                "edge_length": float(self.edge_length),
                "statistics": self.stats,
                "file_path": file_path,
                "created_with": "NaviStore Grid Editor",
            }
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            messagebox.showinfo(
                "Succès",
                f"Grille sauvegardée:\nNom: {layout_hash}.h5\nChemin: {file_path}",
            )
        finally:
            root.destroy()

    def _reset_grid(self):
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
        root = tk.Tk()
        root.withdraw()
        try:
            width = simpledialog.askinteger(
                "Redimensionner",
                "Nouvelle largeur:",
                initialvalue=self.grid_width,
                minvalue=5,
                maxvalue=200,
            )
            if width is None:
                return
            height = simpledialog.askinteger(
                "Redimensionner",
                "Nouvelle hauteur:",
                initialvalue=self.grid_height,
                minvalue=5,
                maxvalue=200,
            )
            if height is None:
                return
            new_grid = np.zeros((height, width), dtype=int)
            copy_height = min(self.grid_height, height)
            copy_width = min(self.grid_width, width)
            new_grid[:copy_height, :copy_width] = self.grid[:copy_height, :copy_width]
            self.grid = new_grid
            self.grid_width, self.grid_height = width, height
            self.has_changes = True
            self._update_stats()
            self._adjust_window_size()
        finally:
            root.destroy()

    def _confirm_action(self, message: str) -> bool:
        root = tk.Tk()
        root.withdraw()
        try:
            return messagebox.askyesno("Confirmation", message)
        finally:
            root.destroy()

    # ------------------------- Mode activation helpers -------------------------
    def _activate_coordinate_mode(self):
        self.coordinate_mode = True
        self.pathfinding_mode = False
        self._reset_pathfinding()

    def _activate_pathfinding_mode(self):
        if not PATHFINDING_AVAILABLE:
            messagebox.showerror(
                "Pathfinding indisponible",
                "Le module pathfinding n'est pas disponible.",
            )
            return
        self.pathfinding_mode = True
        self.coordinate_mode = False
        self._reset_pathfinding()

    def _toggle_infos(self):
        self.infos_visible = not self.infos_visible

    # ------------------------- Pathfinding (unchanged) -------------------------
    def _reset_pathfinding(self):
        self.path_start = None
        self.path_goal = None
        self.computed_path = None
        self.path_stats = None
        self.pathfinding_step = 0

    def _compute_pathfinding(self):
        if not self.path_start or not self.path_goal:
            return
        try:
            poi_coords = np.array([self.path_start, self.path_goal])
            solver = PathfindingSolverFactory.create_solver(
                grid_with_poi=self.grid,
                distance_threshold_grid=1000000.0,
                poi_coords=poi_coords,
                algorithm=self.pathfinding_algorithm,
                diagonal_movement=True,
            )
            start_time = time.time()
            path = solver.find_path(self.path_start, self.path_goal)
            computation_time = time.time() - start_time
            euclidean_dist = np.sqrt(
                (self.path_goal[0] - self.path_start[0]) ** 2
                + (self.path_goal[1] - self.path_start[1]) ** 2
            )
            if path:
                path_distance = 0.0
                for i in range(len(path) - 1):
                    p1, p2 = path[i], path[i + 1]
                    path_distance += np.sqrt(
                        (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2
                    )
                self.path_stats = {
                    "success": True,
                    "algorithm": self.pathfinding_algorithm.upper(),
                    "computation_time": computation_time * 1000,
                    "path_length": len(path),
                    "euclidean_distance": euclidean_dist,
                    "path_distance": path_distance,
                    "efficiency_ratio": (
                        path_distance / euclidean_dist if euclidean_dist > 0 else 0
                    ),
                }
            else:
                self.path_stats = {
                    "success": False,
                    "algorithm": self.pathfinding_algorithm.upper(),
                    "computation_time": computation_time * 1000,
                    "euclidean_distance": euclidean_dist,
                    "error": "No path found",
                }
            self.computed_path = path
            self.pathfinding_step = 2
        except Exception as e:
            self.path_stats = {
                "success": False,
                "error": str(e),
                "algorithm": self.pathfinding_algorithm.upper(),
            }
            print(f"❌ Pathfinding error: {e}")

    # ------------------------- UI drawing -------------------------
    def _draw_menu_bar(self):
        # Draw top menu bar
        menu_rect = pygame.Rect(0, 0, self.screen_width, self.top_menu_height)
        pygame.draw.rect(self.screen, COLORS["menu_bg"], menu_rect)
        x = 8
        for name in self.menu_items:
            text = self.font.render(name, True, COLORS["text"])
            txt_rect = text.get_rect(topleft=(x, 5))
            self.screen.blit(text, txt_rect)
            # Save clickable area
            setattr(
                self,
                f"menu_area_{name}",
                pygame.Rect(x - 4, 0, txt_rect.width + 12, self.top_menu_height),
            )
            x += txt_rect.width + 22

        # Draw dropdown if open
        if self.open_dropdown:
            items = self.dropdowns[self.open_dropdown]
            area_x = getattr(self, f"menu_area_{self.open_dropdown}").x
            area_y = self.top_menu_height
            # Build dropdown rect
            item_h = 22
            width = 260
            height = item_h * len(items)
            dropdown_rect = pygame.Rect(area_x, area_y, width, height)
            pygame.draw.rect(self.screen, COLORS["ui_bg"], dropdown_rect)
            pygame.draw.rect(self.screen, COLORS["grid_line"], dropdown_rect, 1)
            for i, (label, _, _) in enumerate(items):
                y = area_y + i * item_h
                item_rect = pygame.Rect(area_x, y, width, item_h)
                # Hover highlight
                if item_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, COLORS["menu_hover"], item_rect)
                # Draw label
                text = self.small_font.render(label, True, COLORS["text"])
                self.screen.blit(text, (area_x + 6, y + 3))

    def _draw_palette(self):
        # Vertical palette on left side (positioned below the top menu to avoid overlay)
        palette_x = 10
        # Default palette top is below the menu
        palette_y = self.top_menu_height + 8
        item_size = 32
        gap = 10

        # If a dropdown menu is open, push the palette below the dropdown area
        if self.open_dropdown:
            # approximate dropdown item height & total height
            items = self.dropdowns.get(self.open_dropdown, [])
            item_h = 22
            dropdown_height = item_h * max(1, len(items))
            palette_y = self.top_menu_height + dropdown_height + 12

        for i, (label, color, val) in enumerate(self.palette):
            rect = pygame.Rect(
                palette_x, palette_y + i * (item_size + gap), item_size, item_size
            )
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLORS["grid_line"], rect, 2)
            # Draw border for selected
            if self.side_selected_tool == val:
                pygame.draw.rect(self.screen, (0, 120, 215), rect, 3)
            # clickable area store
            setattr(self, f"palette_area_{i}", rect)
            # small label
            label_surf = self.tiny_font.render(label, True, COLORS["text"])
            self.screen.blit(label_surf, (rect.right + 8, rect.y + 6))

    def _draw_grid(self):
        grid_rect = pygame.Rect(
            self.offset_x,
            self.offset_y,
            self.grid_width * self.cell_size,
            self.grid_height * self.cell_size,
        )
        pygame.draw.rect(self.screen, COLORS["background"], grid_rect)
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cell_rect = pygame.Rect(
                    self.offset_x + x * self.cell_size,
                    self.offset_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                cell_value = self.grid[y, x]
                if cell_value == 0:
                    color = COLORS["navigable"]
                elif cell_value == 1:
                    color = COLORS["poi"]
                elif cell_value == 2:
                    color = COLORS["shelf"]
                else:
                    color = COLORS["obstacle"]
                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, COLORS["grid_line"], cell_rect, 1)
        # Zones and pathfinding
        self._draw_zones()
        if self.pathfinding_mode:
            self._draw_pathfinding_elements()

    def _draw_zones(self):
        if not self.zones:
            return
        if hasattr(pygame, "SRCALPHA"):
            zone_surface = pygame.Surface(
                (self.screen_width, self.screen_height), pygame.SRCALPHA
            )
        else:
            zone_surface = pygame.Surface((self.screen_width, self.screen_height))
            zone_surface.set_alpha(80)
        for zone in self.zones:
            if len(zone.points) < 3:
                continue
            screen_points = []
            for x, y in zone.points:
                grid_x = int(x / self.edge_length)
                grid_y = int(y / self.edge_length)
                screen_x = self.offset_x + grid_y * self.cell_size
                screen_y = self.offset_y + grid_x * self.cell_size
                screen_points.append((screen_x, screen_y))
            if len(screen_points) >= 3:
                pygame.draw.polygon(zone_surface, COLORS["zone"][:3], screen_points)
                pygame.draw.polygon(zone_surface, (255, 255, 0), screen_points, 2)
        self.screen.blit(zone_surface, (0, 0))

    def _draw_pathfinding_elements(self):
        if self.computed_path and len(self.computed_path) > 1:
            path_points = []
            for px, py in self.computed_path:
                screen_x = self.offset_x + py * self.cell_size + self.cell_size // 2
                screen_y = self.offset_y + px * self.cell_size + self.cell_size // 2
                path_points.append((screen_x, screen_y))
            if len(path_points) > 1:
                pygame.draw.lines(
                    self.screen, COLORS["path_line"], False, path_points, 3
                )
            for point in path_points[1:-1]:
                pygame.draw.circle(self.screen, COLORS["path_line"], point, 2)
        if self.path_start:
            sx, sy = self.path_start
            start_rect = pygame.Rect(
                self.offset_x + sy * self.cell_size + 2,
                self.offset_y + sx * self.cell_size + 2,
                self.cell_size - 4,
                self.cell_size - 4,
            )
            pygame.draw.rect(self.screen, COLORS["path_start"], start_rect)
        if self.path_goal:
            gx, gy = self.path_goal
            goal_rect = pygame.Rect(
                self.offset_x + gy * self.cell_size + 2,
                self.offset_y + gx * self.cell_size + 2,
                self.cell_size - 4,
                self.cell_size - 4,
            )
            pygame.draw.rect(self.screen, COLORS["path_goal"], goal_rect)

    def _draw_info_panel(self):
        """
        Single grouped Infos panel (toggleable from File menu).
        Positioned below the top menu to avoid any overlay with dropdowns.
        """
        if not self.infos_visible:
            return
        # Place the Info panel to the right of the grid, but ensure its top is below the menu bar
        info_x = self.offset_x + self.grid_width * self.cell_size + 20
        info_y = self.top_menu_height + 8
        info_width = self.ui_panel_width
        # Height limited by available vertical space under the menu
        info_height = min(self.screen_height - info_y - 40, 800)
        info_rect = pygame.Rect(info_x, info_y, info_width, info_height)
        pygame.draw.rect(self.screen, COLORS["ui_bg"], info_rect)
        pygame.draw.rect(self.screen, COLORS["grid_line"], info_rect, 1)
        # Title
        title = self.font.render("Infos — NaviStore", True, COLORS["text"])
        self.screen.blit(title, (info_rect.x + 8, info_rect.y + 8))
        y = info_rect.y + 38
        # Grid information, statistics, tools, shortcuts and legend merged
        grid_info = [
            f"Dimensions: {self.grid_width} × {self.grid_height} cells",
            f"Cell size: {self.edge_length:.1f} cm",
            f"Zoom: {self.cell_size} px/cell",
            "",
            f"Total cellules: {self.grid_width * self.grid_height}",
            f"Zones libres: {self.stats['navigable']}",
            f"Obstacles: {self.stats['obstacles']}",
            f"POIs: {self.stats['pois']}",
            f"Étagères: {self.stats['shelves']}",
            "",
            "Outils (clavier): 1=Libre 2=Obstacle 3=POI 4=Étagère",
            "Glisser pour dessiner. Clic droit applique la couleur sélectionnée à gauche.",
            "",
            "Raccourcis: Ctrl+N,Nouveau | Ctrl+O,Ouvrir | Ctrl+S,Sauver | Ctrl+Q,Quitter",
        ]
        for line in grid_info:
            s = self.small_font.render(line, True, COLORS["text"])
            self.screen.blit(s, (info_rect.x + 10, y))
            y += 18
        # Legend boxes (placed in a new area inside the info panel)
        legend_y = y + 6
        legend_items = [
            ("Libre", COLORS["navigable"], 0),
            ("Obstacle", COLORS["obstacle"], -1),
            ("POI", COLORS["poi"], 1),
            ("Étagère", COLORS["shelf"], 2),
        ]
        # Draw legend vertically to avoid horizontal overflow
        ly = legend_y
        for label, color, val in legend_items:
            r = pygame.Rect(info_rect.x + 10, ly, 18, 18)
            pygame.draw.rect(self.screen, color, r)
            pygame.draw.rect(self.screen, COLORS["grid_line"], r, 1)
            t = self.tiny_font.render(f"{label} ({val})", True, COLORS["text"])
            self.screen.blit(t, (r.right + 6, r.y))
            ly += 22

    def _draw_mode_info_area(self):
        # Dedicated area under main grid for active mode information
        area_x = self.offset_x
        area_y = self.offset_y + self.grid_height * self.cell_size + 10
        area_w = min(
            self.grid_width * self.cell_size, self.screen_width - self.offset_x - 40
        )
        area_h = self.mode_info_height - 20
        area_rect = pygame.Rect(area_x, area_y, area_w, area_h)
        pygame.draw.rect(self.screen, COLORS["ui_bg"], area_rect)
        pygame.draw.rect(self.screen, COLORS["grid_line"], area_rect, 1)
        if self.coordinate_mode:
            title = self.small_font.render(
                "Mode Coordonnées — ACTIF", True, (0, 100, 200)
            )
            self.screen.blit(title, (area_rect.x + 8, area_rect.y + 6))
            if hasattr(self, "last_clicked_cell") and self.last_clicked_cell:
                x, y = self.last_clicked_cell
                wx, wy = self.last_clicked_coords
                lines = [
                    f"Dernière case: ({x},{y})",
                    f"Monde: ({wx:.1f}cm,{wy:.1f}cm)",
                    f"Valeur: {self.grid[x,y]}",
                ]
                yy = area_rect.y + 28
                for l in lines:
                    self.screen.blit(
                        self.small_font.render(l, True, COLORS["text"]),
                        (area_rect.x + 8, yy),
                    )
                    yy += 18
        elif self.pathfinding_mode:
            title = self.small_font.render(
                "Mode Pathfinding — ACTIF", True, (200, 100, 0)
            )
            self.screen.blit(title, (area_rect.x + 8, area_rect.y + 6))
            yy = area_rect.y + 28
            if self.path_stats:
                if self.path_stats.get("success"):
                    lines = [
                        f"Chemin trouvé: {self.path_stats['path_length']} points",
                        f"Distance: {self.path_stats['path_distance']:.2f}",
                        f"Temps: {self.path_stats['computation_time']:.1f} ms",
                    ]
                else:
                    lines = [f"Aucun chemin: {self.path_stats.get('error','')}"]
                for l in lines:
                    self.screen.blit(
                        self.small_font.render(l, True, COLORS["text"]),
                        (area_rect.x + 8, yy),
                    )
                    yy += 18
            if self.path_start:
                self.screen.blit(
                    self.small_font.render(
                        f"Départ: {self.path_start}", True, COLORS["text"]
                    ),
                    (area_rect.x + 8, yy),
                )
                yy += 18
            if self.path_goal:
                self.screen.blit(
                    self.small_font.render(
                        f"Arrivée: {self.path_goal}", True, COLORS["text"]
                    ),
                    (area_rect.x + 8, yy),
                )
                yy += 18
        else:
            title = self.small_font.render("Aucun mode actif", True, COLORS["text"])
            self.screen.blit(title, (area_rect.x + 8, area_rect.y + 6))

    # ------------------------- Input handling -------------------------
    def _get_grid_pos(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        mx, my = mouse_pos
        col = (mx - self.offset_x) // self.cell_size
        row = (my - self.offset_y) // self.cell_size
        if 0 <= col < self.grid_width and 0 <= row < self.grid_height:
            return int(row), int(col)
        return None

    def _handle_menu_click(self, pos: Tuple[int, int]):
        # Toggle dropdown open/close when clicking menu titles
        for name in self.menu_items:
            rect = getattr(self, f"menu_area_{name}")
            if rect.collidepoint(pos):
                if self.open_dropdown == name:
                    self.open_dropdown = None
                else:
                    self.open_dropdown = name
                return True
        # Click within open dropdown
        if self.open_dropdown:
            items = self.dropdowns[self.open_dropdown]
            area_x = getattr(self, f"menu_area_{self.open_dropdown}").x
            area_y = self.top_menu_height
            item_h = 22
            width = 260
            for i, (label, callback, _) in enumerate(items):
                item_rect = pygame.Rect(area_x, area_y + i * item_h, width, item_h)
                if item_rect.collidepoint(pos):
                    # If entry is separator or disabled
                    if callback:
                        callback()
                    self.open_dropdown = None
                    return True
        return False

    def _handle_palette_click(self, pos: Tuple[int, int]) -> bool:
        for i, _ in enumerate(self.palette):
            rect = getattr(self, f"palette_area_{i}")
            if rect.collidepoint(pos):
                _, _, val = self.palette[i]
                self.side_selected_tool = val
                print(f"Palette sélectionnée: {self.palette[i][0]} ({val})")
                return True
        return False

    def _handle_mouse_click(self, pos: Tuple[int, int], button: int):
        # Menu click handling has priority
        if self._handle_menu_click(pos):
            return
        # Palette click handling
        if self._handle_palette_click(pos):
            return
        # Buttons area (legacy) - currently empty
        for ui_button in self.buttons:
            if ui_button["rect"].collidepoint(pos):
                ui_button["callback"]()
                return
        grid_pos = self._get_grid_pos(pos)
        if grid_pos:
            x, y = grid_pos
            # Pathfinding mode handling (left click only)
            if self.pathfinding_mode and button == 1:
                if self.grid[x, y] == -1:
                    print(f"❌ Cannot select obstacle at ({x}, {y})")
                    return
                if self.pathfinding_step == 0:
                    self.path_start = (x, y)
                    self.pathfinding_step = 1
                    print(f"Start selected {self.path_start}")
                elif self.pathfinding_step == 1:
                    if (x, y) == self.path_start:
                        print("Start and goal must differ")
                        return
                    self.path_goal = (x, y)
                    self._compute_pathfinding()
                elif self.pathfinding_step == 2:
                    self._reset_pathfinding()
                    self.path_start = (x, y)
                    self.pathfinding_step = 1
                return
            # Coordinate mode
            if self.coordinate_mode:
                wx, wy = self._calculate_world_coordinates(x, y)
                self.last_clicked_cell = (x, y)
                self.last_clicked_coords = (wx, wy)
                print(
                    f"Cell: {self.last_clicked_cell} World: ({wx:.1f},{wy:.1f}) Val: {self.grid[x,y]}"
                )
                return
            # Normal edit mode
            if not self.pathfinding_mode and not self.coordinate_mode:
                if button == 1:  # left click uses current_tool
                    new_value = self.current_tool
                    # also prepare drag tool
                    self.drag_tool = new_value
                elif button == 3:  # right click uses side_selected_tool
                    new_value = self.side_selected_tool
                    self.drag_tool = new_value
                elif button == 2:
                    new_value = 1
                    self.drag_tool = new_value
                else:
                    return
                if self.grid[x, y] != new_value:
                    self.grid[x, y] = new_value
                    self.has_changes = True
                    self._update_stats()

    def _handle_mouse_drag(self, pos: Tuple[int, int]):
        if self.drag_tool is None:
            return
        grid_pos = self._get_grid_pos(pos)
        if grid_pos:
            x, y = grid_pos
            if self.grid[x, y] != self.drag_tool:
                self.grid[x, y] = self.drag_tool
                self.has_changes = True
                self._update_stats()

    def _handle_mouse_up(self):
        self.drag_tool = None

    # ------------------------- Misc UI helpers -------------------------
    def _adjust_window_size(self):
        grid_display_width = self.grid_width * self.cell_size
        grid_display_height = self.grid_height * self.cell_size
        new_width = max(
            self.min_window_width, grid_display_width + self.ui_panel_width + 200
        )
        new_height = max(
            self.min_window_height, grid_display_height + self.mode_info_height + 200
        )
        self.screen_width = new_width
        self.screen_height = new_height
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )

    def _show_about(self):
        root = tk.Tk()
        root.withdraw()
        try:
            messagebox.showinfo(
                "À propos",
                "NaviStore Grid Editor — Refactorisé\nUI moderne intégrée (Pygame)\nMaintient la logique existante.",
            )
        finally:
            root.destroy()

    def _show_help(self):
        root = tk.Tk()
        root.withdraw()
        try:
            messagebox.showinfo(
                "Aide",
                "Voir le menu Fichier -> Infos pour les raccourcis et la légende. F1 pour aide.",
            )
        finally:
            root.destroy()

    def _quit_editor(self):
        if self.has_changes:
            if not self._confirm_action("Quitter sans sauvegarder les modifications?"):
                return
        self.running = False

    # ------------------------- Keyboard handling -------------------------
    def _handle_keyboard(self, key):
        keys = pygame.key.get_pressed()
        ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        if key == pygame.K_s and ctrl_pressed:
            self._save_grid()
        elif key == pygame.K_o and ctrl_pressed:
            self._load_grid()
        elif key == pygame.K_n and ctrl_pressed:
            self._new_grid()
        elif key == pygame.K_q and ctrl_pressed:
            self._quit_editor()
        elif key == pygame.K_F1:
            self._show_help()
        elif key == pygame.K_p:
            # toggle path mode via keyboard
            if self.pathfinding_mode:
                self.pathfinding_mode = False
                self._reset_pathfinding()
            else:
                self._activate_pathfinding_mode()
        elif key == pygame.K_c:
            self.coordinate_mode = not self.coordinate_mode
            if self.coordinate_mode:
                self.pathfinding_mode = False
                self._reset_pathfinding()
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            if self.cell_size < MAX_CELL_SIZE:
                self.cell_size += 2
                self._adjust_window_size()
        elif key == pygame.K_MINUS:
            if self.cell_size > MIN_CELL_SIZE:
                self.cell_size -= 2
                self._adjust_window_size()
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            if key == pygame.K_1:
                self.current_tool = 0
            elif key == pygame.K_2:
                self.current_tool = -1
            elif key == pygame.K_3:
                self.current_tool = 1
            elif key == pygame.K_4:
                self.current_tool = 2
            print(f"Outil courant: {self.current_tool}")
        elif key == pygame.K_TAB:
            tools = [0, -1, 1, 2]
            current_index = tools.index(self.current_tool)
            self.current_tool = tools[(current_index + 1) % len(tools)]
            print(f"Outil courant: {self.current_tool}")

    # ------------------------- Main loop -------------------------
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit_editor()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in (1, 2, 3):
                        self._handle_mouse_click(event.pos, event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self._handle_mouse_up()
                elif event.type == pygame.MOUSEMOTION:
                    self._handle_mouse_drag(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self._handle_keyboard(event.key)
                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width = max(self.min_window_width, event.w)
                    self.screen_height = max(self.min_window_height, event.h)
                    self.screen = pygame.display.set_mode(
                        (self.screen_width, self.screen_height), pygame.RESIZABLE
                    )

            # Rendering: draw base UI first, then draw menu on top so dropdowns are never occluded
            self.screen.fill(COLORS["background"])
            # Draw palette and grid first
            self._draw_palette()
            self._draw_grid()
            # Draw Info panel and Mode-specific area
            self._draw_info_panel()
            self._draw_mode_info_area()
            # Finally draw the menu bar (so dropdowns are top-most)
            self._draw_menu_bar()

            pygame.display.flip()
            clock.tick(60)
        pygame.quit()


def main():
    try:
        editor = GridEditor()
        editor.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
