#!/usr/bin/env python3
"""
Debug de la conversion de coordonnées spécifique.
"""

import sys
import os
import numpy as np

# Ajouter le chemin vers les modules API
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "api_products"))

try:
    from api_products.path_optimization.utils import real_world_to_grid_coords
except ImportError:
    # Fallback: implémentation directe pour test
    def real_world_to_grid_coords(
        real_coords: np.ndarray, edge_length: float
    ) -> np.ndarray:
        """Version locale pour test."""
        grid_coords = np.floor(real_coords / edge_length).astype(int)
        return grid_coords


def test_specific_conversion():
    """Test la conversion spécifique mentionnée par l'utilisateur."""
    print("🔍 Debug conversion spécifique")
    print("=" * 50)

    # Point problématique
    real_point = np.array([[550.0, 3150.0]])
    edge_length = 100.0

    print(f"Point réel: {real_point[0]}")
    print(f"Edge length: {edge_length}")

    # Conversion avec fonction actuelle
    grid_result = real_world_to_grid_coords(real_point, edge_length)
    print(f"Résultat POIMapper: {grid_result[0]}")

    # Calcul manuel pour vérifier
    manual_x = int(550.0 // 100.0)
    manual_y = int(3150.0 // 100.0)
    print(f"Calcul manuel (floor): ({manual_x}, {manual_y})")

    # Test avec ancienne logique (round - 0.5)
    old_x = int(np.round(550.0 / 100.0 - 0.5))
    old_y = int(np.round(3150.0 / 100.0 - 0.5))
    print(f"Ancienne logique (round - 0.5): ({old_x}, {old_y})")

    print("\n" + "=" * 50)

    # Vérifier quel grid index devrait générer ce point réel
    expected_grid_x = 5  # Selon simulateur
    expected_grid_y = 31  # Selon simulateur

    print(f"Attendu du simulateur: ({expected_grid_x}, {expected_grid_y})")

    # Vérifier la génération inverse
    generated_real_x = (expected_grid_x + 0.5) * edge_length
    generated_real_y = (expected_grid_y + 0.5) * edge_length
    print(f"Point généré par simulateur: ({generated_real_x}, {generated_real_y})")

    # Comparer
    if (generated_real_x, generated_real_y) == (550.0, 3150.0):
        print("✅ La génération simulateur est cohérente")
    else:
        print("❌ Incohérence dans la génération simulateur")


def test_edge_cases():
    """Test des cas limites."""
    print("\n🎯 Test cas limites")
    print("=" * 50)

    edge_length = 100.0

    test_cases = [
        (550.0, 3150.0),  # Votre cas spécifique
        (50.0, 50.0),  # Centre (0,0)
        (150.0, 150.0),  # Centre (1,1)
        (599.0, 599.0),  # Près du bord
        (600.0, 600.0),  # Frontière exacte
    ]

    for real_x, real_y in test_cases:
        real_point = np.array([[real_x, real_y]])
        grid_result = real_world_to_grid_coords(real_point, edge_length)[0]

        # Calcul attendu
        expected_x = int(real_x // edge_length)
        expected_y = int(real_y // edge_length)

        match = tuple(grid_result) == (expected_x, expected_y)
        status = "✅" if match else "❌"

        print(
            f"Real ({real_x}, {real_y}) -> Grid {tuple(grid_result)} (attendu ({expected_x}, {expected_y})) {status}"
        )


if __name__ == "__main__":
    test_specific_conversion()
    test_edge_cases()
