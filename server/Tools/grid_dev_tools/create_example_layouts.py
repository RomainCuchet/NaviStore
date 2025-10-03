"""
Générateur d'exemples de grilles de magasin.

Crée des exemples de layouts de magasin pour tester le système d'optimisation.
"""

import numpy as np
import h5py
import os
from typing import Tuple


def create_simple_store_layout() -> Tuple[np.ndarray, float]:
    """
    Crée un layout simple de magasin.

    Returns:
        Tuple (layout, edge_length)
    """
    # Grille 15x10 - petit magasin
    layout = np.array(
        [
            # Rangées d'allées avec obstacles (rayonnages)
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, 0, 0],
            [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, 0, 0],
            [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, 0, 0],
            [0, -1, -1, -1, 0, -1, -1, -1, 0, -1, -1, -1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
    )

    return layout, 50.0  # 50cm par cellule


def create_complex_store_layout() -> Tuple[np.ndarray, float]:
    """
    Crée un layout complexe de magasin avec différentes zones.

    Returns:
        Tuple (layout, edge_length)
    """
    # Grille 25x20 - grand magasin
    layout = np.zeros((20, 25), dtype=int)

    # Murs extérieurs (premiers et derniers indices)
    layout[0, :] = -1  # Mur haut
    layout[-1, :] = -1  # Mur bas
    layout[:, 0] = -1  # Mur gauche
    layout[:, -1] = -1  # Mur droit

    # Entrée
    layout[-1, 12] = 0
    layout[-1, 13] = 0

    # Rayonnages centraux
    for i in range(2, 18, 3):
        for j in range(3, 22, 4):
            # Rayonnages rectangulaires
            layout[i : i + 2, j : j + 3] = -1

    # Zone caisses (bas droite)
    layout[15:18, 18:23] = -1
    layout[17, 19:22] = 0  # Passages caisses

    # Zone stockage (haut gauche)
    layout[2:6, 2:8] = -1
    layout[4, 3:7] = 0  # Passage central

    # Allées principales
    layout[9, 1:-1] = 0  # Allée centrale horizontale
    layout[1:-1, 12] = 0  # Allée centrale verticale

    return layout, 75.0  # 75cm par cellule


def create_supermarket_layout() -> Tuple[np.ndarray, float]:
    """
    Crée un layout de supermarché réaliste.

    Returns:
        Tuple (layout, edge_length)
    """
    # Grille 30x40 - supermarché
    layout = np.zeros((30, 40), dtype=int)

    # Murs extérieurs
    layout[0, :] = -1
    layout[-1, :] = -1
    layout[:, 0] = -1
    layout[:, -1] = -1

    # Entrées multiples
    layout[-1, 18:22] = 0  # Entrée principale
    layout[-1, 8:10] = 0  # Entrée secondaire

    # Rayonnages longs (supermarchés)
    for i in range(3, 25, 4):
        layout[i : i + 2, 5:35] = -1
        # Passages aux extrémités
        layout[i : i + 2, 35:37] = 0

    # Allées transversales
    for j in range(10, 35, 8):
        layout[1:27, j] = 0

    # Zone fruits et légumes (entrée)
    layout[25:28, 5:15] = -1
    layout[26, 6:14] = 0

    # Zone boucherie/poissonnerie
    layout[5:10, 35:38] = -1

    # Zone boulangerie
    layout[2:5, 2:8] = -1

    # Caisses
    for i in range(20, 28, 2):
        layout[i : i + 1, 25:30] = -1
        layout[i, 30] = 0  # Passage caisse

    # Zone stockage/bureaux
    layout[2:8, 32:38] = -1

    return layout, 100.0  # 1m par cellule


def save_example_layouts():
    """Sauvegarde les exemples de layouts."""
    examples_dir = "../../assets/layout_examples"
    os.makedirs(examples_dir, exist_ok=True)

    layouts = [
        ("simple_store.h5", create_simple_store_layout()),
        ("complex_store.h5", create_complex_store_layout()),
        ("supermarket.h5", create_supermarket_layout()),
    ]

    for filename, (layout, edge_length) in layouts:
        filepath = os.path.join(examples_dir, filename)

        with h5py.File(filepath, "w") as f:
            f.create_dataset("layout", data=layout)
            f.create_dataset("edge_length", data=edge_length)

        # Statistiques
        navigable = np.sum(layout == 0)
        obstacles = np.sum(layout == -1)
        total = layout.size

        print(f"Créé {filename}:")
        print(f"  Taille: {layout.shape}")
        print(f"  Taille cellule: {edge_length}cm")
        print(f"  Zones libres: {navigable} ({navigable/total*100:.1f}%)")
        print(f"  Obstacles: {obstacles} ({obstacles/total*100:.1f}%)")
        print()


if __name__ == "__main__":
    print("Génération des exemples de layouts de magasin...")
    save_example_layouts()
    print("Exemples créés dans le dossier 'examples/'")
    print("\nVous pouvez maintenant:")
    print("1. Lancer l'éditeur: python launch_grid_editor.py")
    print("2. Charger un exemple via 'Ouvrir' dans l'éditeur")
    print("3. Modifier et sauvegarder vos propres layouts")
