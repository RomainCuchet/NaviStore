"""
Testeur d'optimisation de chemin avec interface visuelle.

Charge une grille H5, génère des POIs aléatoires et teste l'API d'optimisation.
"""

import pygame
import numpy as np
import h5py
import requests
import json
import random
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
from typing import List, Tuple, Optional
from config import API_CONFIG, VISUAL_CONFIG, OPTIMIZATION_CONFIG

# Configuration des couleurs
COLORS = {
    "navigable": (255, 255, 255),  # Blanc - zone libre
    "poi": (255, 0, 0),  # Rouge - POI
    "obstacle": (0, 0, 0),  # Noir - obstacle
    "shelf": (139, 69, 19),  # Brown - shelf
    "path": (0, 255, 0),  # Vert - chemin optimal
    "path_highlight": (0, 200, 0),  # Vert foncé - chemin surligné
    "grid_line": (200, 200, 200),  # Gris - lignes de grille
    "background": (240, 240, 240),  # Gris clair - arrière-plan
    "text": (0, 0, 0),  # Noir - texte
    "ui_bg": (250, 250, 250),  # Interface
}

# Configuration par défaut
DEFAULT_CELL_SIZE = VISUAL_CONFIG["cell_size"]
API_BASE_URL = API_CONFIG["base_url"]
API_KEY = API_CONFIG["api_key"]


class PathOptimizationTester:
    """Testeur d'optimisation de chemin avec visualisation."""

    def __init__(self, layout_name: Optional[str] = None):
        """Initialise le testeur.

        Args:
            layout_name: Nom du fichier de layout (sans extension .h5)
        """
        pygame.init()

        # Variables de grille
        self.layout = None
        self.edge_length = 100.0
        self.cell_size = DEFAULT_CELL_SIZE
        self.poi_coords_real = []
        self.poi_coords_grid = []
        self.optimal_path = []
        self.grid_height = 0
        self.grid_width = 0
        self.layout_name = layout_name

        # Interface
        self.screen = None
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.running = True

        # Offset pour centrer la grille
        self.offset_x = 50
        self.offset_y = 50

        print("🚀 Testeur d'optimisation de chemin initialisé")
        if layout_name:
            print(f"📋 Layout spécifié: {layout_name}.h5")
        else:
            print("1. Choisissez un fichier H5 de grille")
        print("2. Le système générera 15 POIs aléatoires")
        print("3. Test automatique de l'API d'optimisation")

    def get_layout_path(self, layout_name: str) -> Optional[str]:
        """Construit le chemin vers un fichier de layout.

        Args:
            layout_name: Nom du layout (sans extension)

        Returns:
            Chemin complet vers le fichier ou None si non trouvé
        """
        # Essayer différents répertoires de layout
        layout_dirs = [
            os.path.join(
                os.path.dirname(__file__), "..", "..", "assets", "layout_examples"
            ),
            os.path.join(os.path.dirname(__file__), "layouts"),
            os.path.join(os.path.dirname(__file__), "..", "layouts"),
            ".",  # Répertoire courant
        ]

        for layout_dir in layout_dirs:
            file_path = os.path.join(layout_dir, f"{layout_name}.h5")
            if os.path.exists(file_path):
                return file_path

        print(f"❌ Layout '{layout_name}.h5' non trouvé dans les répertoires:")
        for layout_dir in layout_dirs:
            print(f"   - {os.path.abspath(layout_dir)}")
        return None

    def choose_grid_file(self) -> Optional[str]:
        """Ouvre un navigateur de fichiers pour choisir une grille H5."""
        root = tk.Tk()
        root.withdraw()

        try:
            file_path = filedialog.askopenfilename(
                title="Choisir une grille H5",
                filetypes=[("Fichiers HDF5", "*.h5"), ("Tous fichiers", "*.*")],
                initialdir=os.path.join(
                    os.path.dirname(__file__), "..", "..", "assets", "layout_examples"
                ),
            )
            return file_path if file_path else None
        finally:
            root.destroy()

    def load_grid_from_h5(self, file_path: str) -> bool:
        """Charge une grille depuis un fichier H5."""
        try:
            with h5py.File(file_path, "r") as f:
                self.layout = np.array(f["layout"])
                self.edge_length = float(f["edge_length"][()])

            self.grid_height, self.grid_width = self.layout.shape
            print(
                f"✅ Grille chargée: {self.grid_width}x{self.grid_height}, edge_length={self.edge_length}cm"
            )
            return True

        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return False

    def generate_random_pois(self, count: int = None) -> List[Tuple[float, float]]:
        """Génère des POIs aléatoires dans les zones libres."""
        if count is None:
            count = VISUAL_CONFIG["poi_count"]
        # Trouver toutes les cellules libres (valeur 0)
        free_cells = np.where(self.layout == 0)
        free_positions = list(
            zip(free_cells[0], free_cells[1])
        )  # (row, col) format = (x, y) format

        if len(free_positions) < count:
            print(f"⚠️ Seulement {len(free_positions)} cellules libres disponibles")
            count = len(free_positions)

        # Choisir aléatoirement des positions
        selected_positions = random.sample(free_positions, count - 1)
        if (29, 19) in free_positions:
            selected_positions.append((29, 19))

        # Convertir en coordonnées monde (centre des cellules)
        poi_coords_real = []
        poi_coords_grid = []

        for x, y in selected_positions:  # x=row, y=col
            # Coordonnées du centre de la cellule - x et y gardent leur signification
            real_x = (x + 0.5) * self.edge_length  # x=row -> real_x
            real_y = (y + 0.5) * self.edge_length  # y=col -> real_y
            poi_coords_real.append((real_x, real_y))
            poi_coords_grid.append(
                (int(x), int(y))
            )  # (row, col) - conversion en int natif

        self.poi_coords_real = poi_coords_real
        self.poi_coords_grid = poi_coords_grid

        print("-" * 30)

        for i in range(len(self.poi_coords_grid)):
            print(f"POI {i}")
            print(f"\treal-world coords: {self.poi_coords_real[i]}")
            print(f"\tgrid coords: {self.poi_coords_grid[i]}")

        print("-" * 30)

        return poi_coords_real

    def call_upload_layout_api(self, file_path: str) -> bool:
        """Appelle l'API pour uploader la grille."""
        try:
            with open(file_path, "rb") as f:
                files = {"layout_file": f}
                headers = {"X-API-Key": API_KEY}

                response = requests.post(
                    f"{API_BASE_URL}/path_optimization/upload_layout",
                    files=files,
                    headers=headers,
                )

            if response.status_code == 200:
                print("✅ Grille uploadée avec succès")
                return True
            else:
                print(f"❌ Erreur upload: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Erreur lors de l'upload: {e}")
            return False

    def call_optimize_path_api(self) -> Optional[List[Tuple[int, int]]]:
        """Appelle l'API d'optimisation et retourne le chemin."""
        try:
            # Préparer la requête
            request_data = {
                "poi_coordinates": [{"x": x, "y": y} for x, y in self.poi_coords_real],
                "distance_threshold": OPTIMIZATION_CONFIG["distance_threshold"],
                "max_runtime": OPTIMIZATION_CONFIG["max_runtime"],
                "include_return_to_start": OPTIMIZATION_CONFIG[
                    "include_return_to_start"
                ],
            }

            headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

            print("🔄 Optimisation en cours...")
            response = requests.post(
                f"{API_BASE_URL}/path_optimization/optimize_path",
                json=request_data,
                headers=headers,
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Optimisation réussie!")
                print(f"   Distance totale: {result['total_distance']:.2f} unités")
                print(f"   Temps de calcul: {result['computation_time']:.2f}s")
                print(f"   Ordre de visite: {result['visiting_order']}")

                # Debug: afficher le format du chemin
                complete_path = result.get("complete_path", [])
                if complete_path:
                    print(
                        f"🔍 Debug: Format du premier point du chemin: {complete_path[0]} (type: {type(complete_path[0])})"
                    )
                    if len(complete_path) > 1:
                        print(
                            f"🔍 Debug: Format du deuxième point: {complete_path[1]} (type: {type(complete_path[1])})"
                        )

                # Extraire le chemin complet
                complete_path = result.get("complete_path", [])
                if complete_path:
                    print(
                        f"🔍 Debug: Nombre de points dans le chemin: {len(complete_path)}"
                    )
                    # Convertir en coordonnées grille
                    path_grid = []
                    for i, point in enumerate(complete_path):
                        # Le point peut être soit un tuple/liste [x, y] soit un dict {"x": x, "y": y}
                        if isinstance(point, (list, tuple)):
                            # Format: [x, y] ou (x, y)
                            x, y = point[0], point[1]
                        elif isinstance(point, dict):
                            # Format: {"x": x, "y": y}
                            x, y = point["x"], point["y"]
                        else:
                            print(
                                f"⚠️ Format de point inconnu: {point} (type: {type(point)})"
                            )
                            continue

                        # Les coordonnées du chemin sont déjà des indices de grille (row, col)
                        # Pas besoin de division par edge_length
                        grid_x = int(x)  # x = row
                        grid_y = int(y)  # y = col

                        # Debug pour les premiers points
                        if i < 3:
                            print(
                                f"🔍 Point {i}: grille=({x}, {y}) -> utilisé=({grid_x}, {grid_y})"
                            )

                        path_grid.append((grid_x, grid_y))

                    print(
                        f"🔍 Debug: Chemin grille généré avec {len(path_grid)} points"
                    )
                    print(
                        f"🔍 Debug: Premiers points du chemin grille: {path_grid[:5]}"
                    )
                    return path_grid

            else:
                print(
                    f"❌ Erreur optimisation: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            print(f"❌ Erreur lors de l'optimisation: {e}")
            return None

    def setup_display(self):
        """Configure l'affichage Pygame."""
        # Calculer taille de la fenêtre
        display_width = self.grid_width * self.cell_size + 200
        display_height = self.grid_height * self.cell_size + 200

        self.screen = pygame.display.set_mode((display_width, display_height))
        pygame.display.set_caption("Testeur d'Optimisation de Chemin - NaviStore")

    def interpolate_path_points(
        self, waypoints: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """Interpole tous les points entre les waypoints pour créer un chemin continu.

        Args:
            waypoints: Liste des points de changement de direction [(row, col), ...]

        Returns:
            Liste complète de tous les points du chemin
        """
        if len(waypoints) < 2:
            return waypoints

        complete_path = []

        for i in range(len(waypoints) - 1):
            start_row, start_col = waypoints[i]
            end_row, end_col = waypoints[i + 1]

            # Ajouter le point de départ (sauf pour le premier segment)
            if i == 0:
                complete_path.append((start_row, start_col))

            # Calculer la direction du mouvement
            delta_row = end_row - start_row
            delta_col = end_col - start_col

            # Déterminer le nombre de pas nécessaires
            steps = max(abs(delta_row), abs(delta_col))

            if steps > 0:
                # Interpoler tous les points intermédiaires
                for step in range(1, steps + 1):
                    interpolated_row = start_row + int(round(delta_row * step / steps))
                    interpolated_col = start_col + int(round(delta_col * step / steps))
                    complete_path.append((interpolated_row, interpolated_col))

        return complete_path

    def draw_grid(self):
        """Dessine la grille avec POIs et chemin."""
        if self.layout is None:
            return

        for y in range(self.grid_height):  # y=row
            for x in range(self.grid_width):  # x=col
                # Position pixel
                pixel_x = self.offset_x + x * self.cell_size
                pixel_y = self.offset_y + y * self.cell_size
                cell_rect = pygame.Rect(
                    pixel_x, pixel_y, self.cell_size, self.cell_size
                )

                # Couleur de base selon le type de cellule
                if self.layout[y, x] == -1:  # matrix[row, col]
                    color = COLORS["obstacle"]
                elif self.layout[y, x] == 2:  # shelf
                    color = COLORS["shelf"]
                else:
                    color = COLORS["navigable"]

                # Dessiner la cellule de base
                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, COLORS["grid_line"], cell_rect, 1)

                # Note: Les POIs sont maintenant dessinés séparément via draw_pois()
                # pour éviter d'être écrasés par les points du chemin

    def draw_path_lines(self):
        """Dessine les lignes du chemin et les waypoints."""
        if len(self.optimal_path) < 2:
            return

        # Dessiner les lignes entre les waypoints
        for i in range(len(self.optimal_path) - 1):
            start_row, start_col = self.optimal_path[i]
            end_row, end_col = self.optimal_path[i + 1]

            # Convertir en coordonnées pixel (centre des cellules)
            start_x = self.offset_x + start_col * self.cell_size + self.cell_size // 2
            start_y = self.offset_y + start_row * self.cell_size + self.cell_size // 2
            end_x = self.offset_x + end_col * self.cell_size + self.cell_size // 2
            end_y = self.offset_y + end_row * self.cell_size + self.cell_size // 2

            # Dessiner la ligne verte fine
            pygame.draw.line(
                self.screen, COLORS["path"], (start_x, start_y), (end_x, end_y), 2
            )

        # Dessiner les points aux waypoints (plus petits pour ne pas écraser les POIs)
        for row, col in self.optimal_path:
            center_x = self.offset_x + col * self.cell_size + self.cell_size // 2
            center_y = self.offset_y + row * self.cell_size + self.cell_size // 2

            # Point vert plus petit avec contour noir
            pygame.draw.circle(self.screen, COLORS["path"], (center_x, center_y), 3)
            pygame.draw.circle(self.screen, COLORS["text"], (center_x, center_y), 3, 1)

    def draw_pois(self):
        """Dessine les POIs par-dessus tout pour qu'ils restent visibles."""
        for i, (row, col) in enumerate(self.poi_coords_grid):
            if 0 <= row < self.grid_height and 0 <= col < self.grid_width:
                center_x = self.offset_x + col * self.cell_size + self.cell_size // 2
                center_y = self.offset_y + row * self.cell_size + self.cell_size // 2
                radius = min(
                    self.cell_size // 3, 10
                )  # Rayon légèrement plus grand pour le texte

                # POI rouge avec contour noir plus épais pour meilleure visibilité
                pygame.draw.circle(
                    self.screen, COLORS["poi"], (center_x, center_y), radius
                )
                pygame.draw.circle(
                    self.screen, COLORS["text"], (center_x, center_y), radius, 2
                )  # Contour noir

                # Afficher le numéro du POI au centre
                poi_number = str(i)
                # Choisir la taille de police en fonction du rayon
                font_size = max(12, min(16, radius))
                number_font = pygame.font.Font(None, font_size)
                text_surface = number_font.render(
                    poi_number, True, COLORS["background"]
                )  # Blanc pour contraste

                # Centrer le texte dans le cercle
                text_rect = text_surface.get_rect(center=(center_x, center_y))
                self.screen.blit(text_surface, text_rect)

    def draw_ui(self):
        """Dessine l'interface utilisateur."""
        # Titre
        title_text = self.font.render(
            "Testeur d'Optimisation de Chemin", True, COLORS["text"]
        )
        self.screen.blit(title_text, (10, 10))

        # Informations
        if self.layout is not None:
            info_texts = [
                f"Grille: {self.grid_width} x {self.grid_height}",
                f"Edge length: {self.edge_length} cm",
                f"POIs générés: {len(self.poi_coords_real)}",
                (
                    f"Waypoints: {len(self.optimal_path)} points"
                    if self.optimal_path
                    else "Pas de chemin calculé"
                ),
            ]

            for i, text in enumerate(info_texts):
                text_surface = self.small_font.render(text, True, COLORS["text"])
                self.screen.blit(text_surface, (10, 40 + i * 20))

        # Légende
        legend_y = self.grid_height * self.cell_size + self.offset_y + 20
        legend_items = [
            ("Zone libre", COLORS["navigable"]),
            ("Obstacle", COLORS["obstacle"]),
            ("Chemin", COLORS["path"]),
            ("POI", COLORS["poi"]),
        ]

        for i, (label, color) in enumerate(legend_items):
            rect = pygame.Rect(10 + i * 120, legend_y, 15, 15)
            if label == "POI":
                # Dessiner un rectangle blanc avec un cercle rouge pour les POIs
                pygame.draw.rect(self.screen, COLORS["navigable"], rect)
                pygame.draw.rect(self.screen, COLORS["grid_line"], rect, 1)
                center_x, center_y = rect.center
                pygame.draw.circle(self.screen, color, (center_x, center_y), 6)
                pygame.draw.circle(
                    self.screen, COLORS["text"], (center_x, center_y), 6, 1
                )
            elif label == "Chemin":
                # Dessiner un rectangle blanc avec une ligne et un point vert
                pygame.draw.rect(self.screen, COLORS["navigable"], rect)
                pygame.draw.rect(self.screen, COLORS["grid_line"], rect, 1)
                # Ligne verte
                pygame.draw.line(
                    self.screen,
                    color,
                    (rect.left + 2, rect.centery),
                    (rect.right - 2, rect.centery),
                    2,
                )
                # Points verts aux extrémités
                pygame.draw.circle(self.screen, color, (rect.left + 3, rect.centery), 3)
                pygame.draw.circle(
                    self.screen, color, (rect.right - 3, rect.centery), 3
                )
            else:
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, COLORS["grid_line"], rect, 1)

            text = self.small_font.render(label, True, COLORS["text"])
            self.screen.blit(text, (30 + i * 120, legend_y))

    def run_test(self):
        """Lance le test complet."""
        # 1. Déterminer le fichier de layout
        if self.layout_name:
            # Layout spécifié en paramètre
            file_path = self.get_layout_path(self.layout_name)
            if not file_path:
                return
            print(f"📂 Utilisation du layout: {file_path}")
        else:
            # Choisir fichier interactivement
            file_path = self.choose_grid_file()
            if not file_path:
                print("❌ Aucun fichier sélectionné")
                return

        # 2. Charger grille
        if not self.load_grid_from_h5(file_path):
            return

        # 3. Générer POIs
        self.generate_random_pois()

        # 4. Setup display
        self.setup_display()

        # 5. Upload layout
        if not self.call_upload_layout_api(file_path):
            print("❌ Impossible d'uploader la grille")
            return

        # 6. Optimiser chemin
        optimal_path = self.call_optimize_path_api()
        if optimal_path:
            self.optimal_path = optimal_path
            print(f"✅ Test terminé! Chemin optimal avec {len(optimal_path)} points")
            print(f"🔍 Debug: POIs grille: {self.poi_coords_grid[:5]}")
            print(f"🔍 Debug: Chemin grille: {optimal_path[:5]}")
            print("✅ Visualisation du résultat...")
        else:
            print("⚠️ Pas de chemin optimal calculé, affichage des POIs seulement")

        # 7. Affichage
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # Rendu avec ordre spécifique pour visibilité
            self.screen.fill(COLORS["background"])
            self.draw_grid()  # 1. Grille et obstacles
            self.draw_path_lines()  # 2. Chemin (lignes et points verts)
            self.draw_pois()  # 3. POIs par-dessus tout (points rouges)
            self.draw_ui()  # 4. Interface utilisateur
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


def main():
    """Point d'entrée principal."""
    import sys

    layout_name = None
    if len(sys.argv) > 1:
        layout_name = sys.argv[1]
        print(f"📋 Layout spécifié en paramètre: {layout_name}")

    try:
        tester = PathOptimizationTester(layout_name=layout_name)
        tester.run_test()
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Afficher l'aide si --help est demandé
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python path_optimization_tester.py [layout_name]")
        print("")
        print("Arguments:")
        print("  layout_name    Nom du fichier layout (sans .h5) à utiliser")
        print("                 Si non spécifié, un navigateur de fichiers s'ouvrira")
        print("")
        print("Exemples:")
        print("  python path_optimization_tester.py simple_store")
        print("  python path_optimization_tester.py supermarket")
        print("  python path_optimization_tester.py complex_store")
        exit(0)

    main()
