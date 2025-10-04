"""
Store Layout Grid Editor

Interface Pygame pour éditer les grilles de magasin utilisées par le système d'optimisation de chemin.
Permet de créer, modifier et sauvegarder des layouts avec zones libres, obstacles et POI.

Contrôles:
- Clic gauche: Placer zone libre (0)
- Clic droit: Placer obstacle (-1)
- Clic milieu: Placer POI (1)
- S: Sauvegarder
- R: Réinitialiser
- ESC: Quitter sans sauvegarder
- +/-: Ajuster la taille de la grille
- Flèches: Déplacer la vue
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

# Imports pour le pathfinding
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from api_products.path_optimization.pathfinding_solver import (
        PathfindingSolver,
        PathfindingSolverFactory,
    )

    PATHFINDING_AVAILABLE = True
except ImportError as e:
    PATHFINDING_AVAILABLE = False
    print(f"⚠️ Pathfinding non disponible: {e}")

# Configuration des couleurs
COLORS = {
    "navigable": (255, 255, 255),  # Blanc - zone libre (0)
    "poi": (0, 255, 0),  # Vert - point d'intérêt (1)
    "obstacle": (0, 0, 0),  # Noir - obstacle (-1)
    "grid_line": (128, 128, 128),  # Gris - lignes de grille
    "background": (200, 200, 200),  # Gris clair - arrière-plan
    "ui_bg": (240, 240, 240),  # Gris très clair - interface
    "text": (0, 0, 0),  # Noir - texte
    "button": (180, 180, 180),  # Gris - boutons
    "button_hover": (160, 160, 160),  # Gris foncé - boutons survolés
    # Couleurs pour le pathfinding
    "path_start": (255, 0, 0),  # Rouge - point de départ
    "path_goal": (0, 0, 255),  # Bleu - point d'arrivée
    "path_line": (255, 165, 0),  # Orange - chemin
    "path_bg": (255, 255, 200),  # Jaune clair - arrière-plan chemin
}

# Configuration par défaut
DEFAULT_GRID_SIZE = (20, 15)
DEFAULT_CELL_SIZE = 25
DEFAULT_EDGE_LENGTH = 100.0  # cm
MIN_CELL_SIZE = 10
MAX_CELL_SIZE = 50


class GridEditor:
    """Éditeur de grille de magasin avec interface Pygame."""

    def __init__(self):
        """Initialise l'éditeur de grille."""
        pygame.init()

        # Configuration de l'affichage
        self.cell_size = DEFAULT_CELL_SIZE
        self.grid_width, self.grid_height = DEFAULT_GRID_SIZE
        self.edge_length = DEFAULT_EDGE_LENGTH

        # Interface utilisateur
        self.ui_panel_width = 350  # Largeur panneau info
        self.ui_height = 120  # Hauteur zone boutons
        self.min_window_width = 800
        self.min_window_height = 600

        # Calculer dimensions fenêtre
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

        # Fontes pour le texte
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.tiny_font = pygame.font.Font(None, 16)

        # État de la grille
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
        self.original_grid = None
        self.has_changes = False

        # Décalage pour la vue
        self.offset_x = 50
        self.offset_y = 50

        # État de l'interface
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

        # Boutons de l'interface
        self.buttons = self._create_buttons()

        # Statistiques
        self.stats = {"navigable": 0, "obstacles": 0, "pois": 0}

        print("Store Layout Grid Editor initialisé")
        print("Contrôles:")
        print("  Clic gauche: Zone libre (blanc)")
        print("  Clic droit: Obstacle (noir)")
        print("  Clic milieu: POI (vert)")
        print("  S: Sauvegarder")
        print("  R: Réinitialiser")
        print("  ESC: Quitter")
        print("  +/-: Ajuster taille cellules")

    def _create_buttons(self) -> list:
        """Crée les boutons de l'interface."""
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
        """Met à jour les statistiques de la grille."""
        unique, counts = np.unique(self.grid, return_counts=True)
        stats_dict = dict(zip(unique, counts))

        self.stats = {
            "navigable": int(stats_dict.get(0, 0)),
            "obstacles": int(stats_dict.get(-1, 0)),
            "pois": int(stats_dict.get(1, 0)),
        }

    def _calculate_layout_hash(self) -> str:
        """Calcule le hash XXH3 64-bit de la grille pour un nom de fichier unique."""
        # Créer les données comme dans le système d'optimisation
        grid_bytes = self.grid.astype(np.int8).tobytes()
        edge_length_bytes = np.array([self.edge_length], dtype=np.float64).tobytes()

        # Combiner les données
        combined_data = grid_bytes + edge_length_bytes

        # Calculer le hash XXH3 64-bit
        hasher = xxhash.xxh3_64()
        hasher.update(combined_data)

        return hasher.hexdigest()

    def _get_grid_pos(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Convertit position souris en coordonnées grille (x=row, y=col)."""
        mx, my = mouse_pos

        # mx correspond aux colonnes (y), my correspond aux lignes (x)
        col = (mx - self.offset_x) // self.cell_size  # y coordinate
        row = (my - self.offset_y) // self.cell_size  # x coordinate

        if 0 <= col < self.grid_width and 0 <= row < self.grid_height:
            return int(row), int(col)  # Retourne (x=row, y=col)
        return None

    def _draw_grid(self):
        """Dessine la grille principale."""
        # Arrière-plan de la grille
        grid_rect = pygame.Rect(
            self.offset_x,
            self.offset_y,
            self.grid_width * self.cell_size,
            self.grid_height * self.cell_size,
        )
        pygame.draw.rect(self.screen, COLORS["background"], grid_rect)

        # Dessiner les cellules
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cell_rect = pygame.Rect(
                    self.offset_x + x * self.cell_size,
                    self.offset_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )

                # Couleur selon le type de cellule
                cell_value = self.grid[y, x]
                if cell_value == 0:
                    color = COLORS["navigable"]
                elif cell_value == 1:
                    color = COLORS["poi"]
                else:  # -1
                    color = COLORS["obstacle"]

                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, COLORS["grid_line"], cell_rect, 1)

        # Dessiner les éléments de pathfinding si actifs
        if self.pathfinding_mode:
            self._draw_pathfinding_elements()

    def _draw_pathfinding_elements(self):
        """Dessine les éléments du pathfinding (start, goal, chemin)."""
        # Dessiner le chemin en premier (sous les points)
        if self.computed_path and len(self.computed_path) > 1:
            # Convertir le chemin en coordonnées écran
            path_points = []
            for px, py in self.computed_path:
                screen_x = self.offset_x + py * self.cell_size + self.cell_size // 2
                screen_y = self.offset_y + px * self.cell_size + self.cell_size // 2
                path_points.append((screen_x, screen_y))

            # Dessiner les lignes du chemin
            if len(path_points) > 1:
                pygame.draw.lines(
                    self.screen, COLORS["path_line"], False, path_points, 3
                )

            # Dessiner des points sur le chemin
            for point in path_points[1:-1]:  # Exclure start et goal
                pygame.draw.circle(self.screen, COLORS["path_line"], point, 2)

        # Dessiner le point de départ
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

            # Label "S" pour Start
            if self.cell_size >= 20:
                font_size = min(self.cell_size - 8, 24)
                font = pygame.font.Font(None, font_size)
                text = font.render("S", True, (255, 255, 255))
                text_rect = text.get_rect(center=start_rect.center)
                self.screen.blit(text, text_rect)

        # Dessiner le point d'arrivée
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

            # Label "G" pour Goal
            if self.cell_size >= 20:
                font_size = min(self.cell_size - 8, 24)
                font = pygame.font.Font(None, font_size)
                text = font.render("G", True, (255, 255, 255))
                text_rect = text.get_rect(center=goal_rect.center)
                self.screen.blit(text, text_rect)

    def _draw_ui(self):
        """Dessine l'interface utilisateur."""
        # Calculer position panneau info
        grid_display_width = self.grid_width * self.cell_size
        info_x = self.offset_x + grid_display_width + 20
        info_width = self.ui_panel_width
        info_height = min(self.screen_height - self.ui_height - 40, 600)

        # Panneau d'informations principal
        info_rect = pygame.Rect(info_x, self.offset_y, info_width, info_height)
        pygame.draw.rect(self.screen, COLORS["ui_bg"], info_rect)
        pygame.draw.rect(self.screen, COLORS["grid_line"], info_rect, 2)

        # Titre avec version
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

        # Section Informations Grille
        self._draw_section_title(
            "Informations Grille", info_rect.x + 10, info_rect.y + y_offset
        )
        y_offset += section_spacing

        grid_info = [
            f"Dimensions: {self.grid_width} × {self.grid_height} cellules",
            f"Taille cellule: {self.edge_length:.1f} cm",
            f"Surface totale: {(self.grid_width * self.edge_length / 100):.1f} × {(self.grid_height * self.edge_length / 100):.1f} m",
            f"Zoom actuel: {self.cell_size} pixels/cellule",
        ]

        for text in grid_info:
            text_surface = self.small_font.render(text, True, COLORS["text"])
            self.screen.blit(text_surface, (info_rect.x + 15, info_rect.y + y_offset))
            y_offset += line_spacing

        y_offset += 10

        # Section Statistiques
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

        # Section Outils
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

        # Section Raccourcis
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

        # Section Légende des couleurs
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

        # Section Mode Coordonnées
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

        # Section Mode Pathfinding
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
            # Pathfinding non disponible
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

        # Indicateur de modifications en haut
        if self.has_changes:
            changes_text = self.font.render(
                "⚠️ Modifications non sauvées", True, (255, 0, 0)
            )
            self.screen.blit(changes_text, (10, 10))
        else:
            saved_text = self.small_font.render("✅ Sauvegardé", True, (0, 150, 0))
            self.screen.blit(saved_text, (10, 15))

    def _draw_section_title(self, title: str, x: int, y: int, color=None):
        """Dessine un titre de section."""
        if color is None:
            color = COLORS["text"]

        # Fond coloré pour le titre
        title_surface = self.font.render(title, True, color)
        title_rect = pygame.Rect(
            x - 5, y - 2, title_surface.get_width() + 10, title_surface.get_height() + 4
        )
        pygame.draw.rect(self.screen, (220, 220, 220), title_rect)
        pygame.draw.rect(self.screen, COLORS["grid_line"], title_rect, 1)
        self.screen.blit(title_surface, (x, y))

    def _draw_buttons(self):
        """Dessine les boutons de l'interface."""
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            # Vérifier survol
            button["hovered"] = button["rect"].collidepoint(mouse_pos)

            # Couleur spéciale pour les boutons actifs
            if button["text"] == "Coord" and self.coordinate_mode:
                color = (100, 150, 255)  # Bleu pour mode actif
                text_color = (255, 255, 255)  # Texte blanc
            elif button["text"] == "Path" and self.pathfinding_mode:
                color = (255, 150, 50)  # Orange pour mode pathfinding actif
                text_color = (255, 255, 255)  # Texte blanc
            elif button["text"] == "Path" and not PATHFINDING_AVAILABLE:
                color = (120, 120, 120)  # Gris pour pathfinding indisponible
                text_color = (200, 200, 200)  # Texte gris clair
            else:
                color = (
                    COLORS["button_hover"] if button["hovered"] else COLORS["button"]
                )
                text_color = COLORS["text"]

            # Dessiner bouton
            pygame.draw.rect(self.screen, color, button["rect"])
            pygame.draw.rect(self.screen, COLORS["grid_line"], button["rect"], 2)

            # Texte du bouton
            text_surface = self.small_font.render(button["text"], True, text_color)
            text_rect = text_surface.get_rect(center=button["rect"].center)
            self.screen.blit(text_surface, text_rect)

    def _handle_mouse_click(self, pos: Tuple[int, int], button: int):
        """Gère les clics de souris."""
        # Vérifier clics sur boutons
        for ui_button in self.buttons:
            if ui_button["rect"].collidepoint(pos):
                ui_button["callback"]()
                return

        # Obtenir position dans la grille
        grid_pos = self._get_grid_pos(pos)
        if grid_pos:
            x, y = grid_pos  # x=row, y=col

            # Mode pathfinding : gestion des points start/goal
            if self.pathfinding_mode and button == 1:  # Clic gauche seulement
                # Vérifier que la cellule est libre
                if self.grid[x, y] == -1:  # Obstacle
                    print(f"❌ Impossible de sélectionner un obstacle en ({x}, {y})")
                    return

                if self.pathfinding_step == 0:  # Choisir start
                    self.path_start = (x, y)
                    self.pathfinding_step = 1
                    print(
                        f"🚀 Point de départ sélectionné: ({x}, {y}) - Cliquez pour choisir l'arrivée"
                    )

                elif self.pathfinding_step == 1:  # Choisir goal
                    if (x, y) == self.path_start:
                        print(
                            "⚠️ Le point d'arrivée doit être différent du point de départ"
                        )
                        return

                    self.path_goal = (x, y)
                    print(
                        f"🎯 Point d'arrivée sélectionné: ({x}, {y}) - Calcul du chemin..."
                    )

                    # Calculer le chemin automatiquement
                    self._compute_pathfinding()

                elif self.pathfinding_step == 2:  # Chemin calculé, recommencer
                    print("🔄 Nouveau test - Cliquez pour choisir le point de départ")
                    self._reset_pathfinding()
                    self.path_start = (x, y)
                    self.pathfinding_step = 1
                    print(
                        f"🚀 Point de départ sélectionné: ({x}, {y}) - Cliquez pour choisir l'arrivée"
                    )

                return

            # Mode coordonnées : afficher les informations
            if self.coordinate_mode:
                world_x, world_y = self._calculate_world_coordinates(x, y)
                self.last_clicked_cell = (x, y)
                self.last_clicked_coords = (world_x, world_y)

                # Afficher dans la console
                print(f"🎯 Coordonnées de la case:")
                print(f"   Grille: (x={x}, y={y}) = (row={x}, col={y})")
                print(f"   Monde: ({world_x:.1f}cm, {world_y:.1f}cm)")
                print(f"   Valeur: {self.grid[x, y]}")
                return

            # Mode édition normal (si pas pathfinding ni coordonnées)
            if not self.pathfinding_mode and not self.coordinate_mode:
                # Déterminer la valeur selon le bouton
                if button == 1:  # Clic gauche - zone libre
                    new_value = 0
                elif button == 3:  # Clic droit - obstacle
                    new_value = -1
                elif button == 2:  # Clic milieu - POI
                    new_value = 1
                else:
                    return

                # Appliquer modification
                if self.grid[x, y] != new_value:  # grid[row, col]
                    self.grid[x, y] = new_value
                    self.has_changes = True
                    self._update_stats()

    def _handle_mouse_drag(self, pos: Tuple[int, int]):
        """Gère le glissement de souris."""
        if self.mouse_pressed:
            grid_pos = self._get_grid_pos(pos)
            if grid_pos:
                x, y = grid_pos  # x=row, y=col selon nouvelle convention

                # Utiliser l'outil actuel
                if self.grid[x, y] != self.current_tool:
                    self.grid[x, y] = self.current_tool
                    self.has_changes = True
                    self._update_stats()

    def _new_grid(self):
        """Crée une nouvelle grille."""
        if self.has_changes:
            if not self._confirm_action(
                "Créer une nouvelle grille? Les modifications non sauvées seront perdues."
            ):
                return

        # Demander les dimensions
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
        """Charge une grille depuis un fichier HDF5."""
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

                    # Récupérer le hash stocké s'il existe
                    stored_hash = f.attrs.get("layout_hash", "Non disponible")

                self.grid = layout
                self.grid_height, self.grid_width = layout.shape
                self.edge_length = edge_length
                self.original_grid = layout.copy()
                self.has_changes = False
                self._update_stats()

                # Calculer le hash actuel pour vérification
                current_hash = self._calculate_layout_hash()

                # Vérifier l'intégrité
                hash_match = (
                    stored_hash != "Non disponible" and stored_hash == current_hash
                )

                # Extraire le nom de fichier pour affichage
                filename = os.path.basename(file_path)

                # Ajuster la fenêtre
                self._adjust_window_size()

                # Message de succès avec informations détaillées
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
        """Sauvegarde la grille actuelle avec hash XXH3 64-bit comme nom."""
        root = tk.Tk()
        root.withdraw()

        try:
            # Calculer le hash XXH3 64-bit de la grille
            layout_hash = self._calculate_layout_hash()

            # Proposer un répertoire de sauvegarde
            save_dir = filedialog.askdirectory(
                title="Choisir le répertoire de sauvegarde",
                initialdir=os.path.join(
                    os.path.dirname(__file__), "..", "assets", "layouts"
                ),
            )

            if save_dir:
                # Créer le nom de fichier basé sur le hash
                file_path = os.path.join(save_dir, f"{layout_hash}.h5")

                # Vérifier si le fichier existe déjà
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

                    # Ajouter le hash comme attribut pour vérification
                    f.attrs["layout_hash"] = layout_hash
                    f.attrs["created_with"] = "NaviStore Grid Editor"

                self.original_grid = self.grid.copy()
                self.has_changes = False

                # Sauvegarder aussi les métadonnées avec le même nom
                metadata_file = os.path.join(save_dir, f"{layout_hash}_metadata.json")

                # Convertir les types NumPy en types Python natifs pour JSON
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
        """Remet la grille à son état d'origine."""
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
        """Redimensionne la grille."""
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

            # Créer nouvelle grille avec redimensionnement
            new_grid = np.zeros((height, width), dtype=int)

            # Copier l'ancienne grille (tronquer ou étendre selon besoin)
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
        """Ajuste la taille de la fenêtre selon la grille."""
        # Calculer nouvelles dimensions
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

        # Recréer les boutons avec nouvelles positions
        self.buttons = self._create_buttons()

        # Mettre à jour les statistiques
        self._update_stats()

    def _confirm_action(self, message: str) -> bool:
        """Affiche une boîte de confirmation."""
        root = tk.Tk()
        root.withdraw()
        try:
            result = messagebox.askyesno("Confirmation", message)
            return result
        finally:
            root.destroy()

    def _toggle_pathfinding_mode(self):
        """Active/désactive le mode pathfinding."""
        if not PATHFINDING_AVAILABLE:
            messagebox.showerror(
                "Pathfinding indisponible",
                "Le module pathfinding n'est pas disponible.\nInstallez avec: pip install pathfinding",
            )
            return

        self.pathfinding_mode = not self.pathfinding_mode

        if self.pathfinding_mode:
            # Désactiver le mode coordonnées s'il est actif
            self.coordinate_mode = False
            # Réinitialiser l'état du pathfinding
            self._reset_pathfinding()
            print(
                "🎯 Mode pathfinding activé - Cliquez pour choisir le point de départ"
            )
        else:
            self._reset_pathfinding()
            print("🔘 Mode pathfinding désactivé")

    def _reset_pathfinding(self):
        """Remet à zéro l'état du pathfinding."""
        self.path_start = None
        self.path_goal = None
        self.computed_path = None
        self.path_stats = None
        self.pathfinding_step = 0

    def _compute_pathfinding(self):
        """Calcule le chemin entre start et goal."""
        if not self.path_start or not self.path_goal:
            return

        try:
            # Créer le solver
            poi_coords = np.array([self.path_start, self.path_goal])

            solver = PathfindingSolverFactory.create_solver(
                grid_with_poi=self.grid,
                jps_cache={},
                distance_threshold_grid=1000000.0,  # Seuil très élevé
                poi_coords=poi_coords,
                algorithm=self.pathfinding_algorithm,
                diagonal_movement=True,
            )

            # Calculer le chemin
            start_time = time.time()
            path = solver.find_path(self.path_start, self.path_goal)
            computation_time = time.time() - start_time

            # Calculer statistiques
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
                    f"✅ Chemin trouvé: {len(path)} points, distance: {path_distance:.2f}"
                )
            else:
                self.path_stats = {
                    "success": False,
                    "algorithm": self.pathfinding_algorithm.upper(),
                    "computation_time": computation_time * 1000,
                    "euclidean_distance": euclidean_dist,
                    "error": "Aucun chemin trouvé",
                }
                print("❌ Aucun chemin trouvé")

            self.computed_path = path
            self.pathfinding_step = 2

        except Exception as e:
            self.path_stats = {
                "success": False,
                "error": str(e),
                "algorithm": self.pathfinding_algorithm.upper(),
            }
            print(f"❌ Erreur pathfinding: {e}")

    def _toggle_coordinate_mode(self):
        """Active/désactive le mode coordonnées."""
        self.coordinate_mode = not self.coordinate_mode
        if self.coordinate_mode:
            self.last_clicked_cell = None
            self.last_clicked_coords = None

    def _calculate_world_coordinates(
        self, grid_x: int, grid_y: int
    ) -> Tuple[float, float]:
        """Calcule les coordonnées monde (centre de la case) à partir des indices de grille.
        Args:
            grid_x: row (ligne)
            grid_y: col (colonne)
        Returns:
            (world_x, world_y) où world_x correspond à grid_x et world_y à grid_y
        """
        # Coordonnées du centre de la case en centimètres
        # grid_x (row) -> world_x, grid_y (col) -> world_y
        world_x = (grid_x + 0.5) * self.edge_length
        world_y = (grid_y + 0.5) * self.edge_length
        return world_x, world_y

    def _show_help(self):
        """Affiche l'aide de l'éditeur."""
        help_text = """AIDE - ÉDITEUR DE GRILLE

OUTILS DE DESSIN:
• Clic gauche: Placer zone navigable (blanc)
• Clic droit: Placer obstacles (noir)
• Clic milieu: Placer POI (rouge)

CONTRÔLES CLAVIER:
• S: Sauvegarder
• R: Reset grille
• ESC: Quitter
• +/-: Ajuster taille cellules
• Flèches: Déplacer vue

BOUTONS:
• Nouveau: Créer nouvelle grille
• Ouvrir: Charger grille existante
• Sauver: Sauvegarder grille actuelle
• Reset: Vider la grille
• Taille: Redimensionner grille
• Coord: Mode coordonnées (affichage)
• Aide: Afficher cette aide
• Quitter: Fermer l'éditeur

MODE COORDONNÉES:
• Activez avec le bouton 'Coord'
• Cliquez sur une case pour voir:
  - Position grille (x, y)
  - Coordonnées monde (cm)
  - Type de cellule
• Désactive l'édition temporairement

LÉGENDE:
• Blanc: Zone navigable (valeur 0)
• Noir: Obstacle (valeur -1)
• Rouge: Point d'intérêt/POI (valeur 1)

FORMAT DE SAUVEGARDE:
• Fichiers nommés avec hash XXH3 64-bit
• Format HDF5 avec métadonnées
• Compatible avec le système d'optimisation
• Vérification d'intégrité automatique

EXEMPLE: a1b2c3d4e5f6.h5
Le nom correspond au hash XXH3 du contenu."""

        self._show_info_dialog(help_text, "Aide")

    def _quit_editor(self):
        """Quitte l'éditeur."""
        if self.has_changes:
            if not self._confirm_action("Quitter sans sauvegarder les modifications?"):
                return
        self.running = False

    def _handle_keyboard(self, key):
        """Gère les entrées clavier."""
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
            # Barre espace pour recommencer le pathfinding
            self._reset_pathfinding()

    def _show_help(self):
        """Affiche l'aide."""
        root = tk.Tk()
        root.withdraw()

        help_text = """
Éditeur de Grille NaviStore - Aide

OUTILS DE DESSIN:
• Clic gauche: Zone libre (navigable) - valeur 0
• Clic droit: Obstacle (mur, rayonnage) - valeur -1  
• Clic milieu: Point d'intérêt (POI) - valeur 1
• Glisser: Dessiner en continu

RACCOURCIS CLAVIER:
• S: Sauvegarder la grille
• R: Réinitialiser/Reset
• ESC: Quitter l'éditeur
• Ctrl+N: Nouvelle grille
• Ctrl+O: Ouvrir fichier
• +/-: Ajuster le zoom
• F1: Afficher cette aide
• P: Activer/désactiver mode pathfinding
• C: Activer/désactiver mode coordonnées
• ESPACE: Reset pathfinding (si mode actif)

BOUTONS:
• Nouveau: Créer une grille (dimensions personnalisées)
• Ouvrir: Charger depuis fichier .h5
• Sauver: Sauvegarder au format .h5
• Reset: Annuler modifications
• Taille: Redimensionner la grille
• Coord: Mode coordonnées (affichage infos)
• Path: Mode pathfinding (test de chemins)
• Quitter: Fermer l'éditeur

MODE PATHFINDING:
• Activez avec bouton 'Path' ou touche 'P'
• 1. Cliquez sur case libre pour point de départ
• 2. Cliquez sur case libre pour point d'arrivée
• 3. Le chemin s'affiche automatiquement
• Statistiques: longueur, distance, temps calcul
• Visualisation: ligne orange, points rouge/bleu
• Cliquez n'importe où pour recommencer

CONSEILS:
• Utilisez des allées de 1-2 cellules de large
• Respectez les proportions réelles d'un magasin
• Testez la navigation entre tous les POIs
• Le pathfinding aide à valider la connectivité
• Sauvegardez régulièrement votre travail
        """

        try:
            messagebox.showinfo("Aide - Éditeur de Grille", help_text)
        finally:
            root.destroy()

    def run(self):
        """Boucle principale de l'éditeur."""
        clock = pygame.time.Clock()

        while self.running:
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit_editor()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in [1, 2, 3]:  # Gauche, milieu, droit
                        self._handle_mouse_click(event.pos, event.button)
                        self.mouse_pressed = True

                        # Définir l'outil actuel pour le glissement
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
                    # Gérer le redimensionnement de la fenêtre
                    self.screen_width = max(self.min_window_width, event.w)
                    self.screen_height = max(self.min_window_height, event.h)
                    self.screen = pygame.display.set_mode(
                        (self.screen_width, self.screen_height), pygame.RESIZABLE
                    )
                    self.buttons = self._create_buttons()

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
        editor = GridEditor()
        editor.run()
    except Exception as e:
        print(f"Erreur fatale: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
