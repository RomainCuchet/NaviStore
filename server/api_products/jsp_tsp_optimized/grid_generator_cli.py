#!/usr/bin/env python3
"""
Générateur de grilles HDF5 en ligne de commande
Script simple pour créer des grilles au format JPS/TSP
"""

import h5py
import numpy as np
import argparse
import json
import sys


def create_empty_grid(width, height, hedge_size=1.0):
    """Crée une grille vide"""
    grid = np.zeros((height, width), dtype=np.int8)
    return grid, []


def create_random_grid(width, height, hedge_size=1.0, obstacle_ratio=0.2, num_poi=5):
    """Crée une grille avec des obstacles aléatoires"""
    # Grille avec obstacles aléatoires
    grid = np.random.choice([0, -1], size=(height, width), 
                          p=[1-obstacle_ratio, obstacle_ratio]).astype(np.int8)
    
    # Ajouter des points d'intérêt aléatoires
    points_of_interest = []
    attempts = 0
    while len(points_of_interest) < num_poi and attempts < num_poi * 10:
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        if grid[y, x] == 0:  # Cellule libre
            points_of_interest.append((x, y))
        attempts += 1
    
    return grid, points_of_interest


def create_maze_grid(width, height, hedge_size=1.0):
    """Crée un labyrinthe simple"""
    grid = np.full((height, width), -1, dtype=np.int8)  # Tout en obstacles
    
    # Créer des couloirs
    for y in range(1, height-1, 2):
        for x in range(1, width-1, 2):
            grid[y, x] = 0  # Cellule libre
            
            # Créer une ouverture aléatoire
            if x < width - 2 and np.random.random() > 0.5:
                grid[y, x+1] = 0
            if y < height - 2 and np.random.random() > 0.5:
                grid[y+1, x] = 0
    
    # Ajouter quelques points d'intérêt
    points_of_interest = []
    free_cells = np.where(grid == 0)
    if len(free_cells[0]) > 0:
        num_poi = min(4, len(free_cells[0]))
        indices = np.random.choice(len(free_cells[0]), num_poi, replace=False)
        for idx in indices:
            y, x = free_cells[0][idx], free_cells[1][idx]
            points_of_interest.append((x, y))
    
    return grid, points_of_interest


def create_store_layout(width, height, hedge_size=1.0):
    """Crée un layout de magasin avec des rayons"""
    grid = np.zeros((height, width), dtype=np.int8)
    
    # Rayons horizontaux
    for y in range(5, height-5, 8):
        for x in range(5, width-5):
            if x % 10 != 0:  # Laisser des passages
                grid[y:y+3, x] = -1
    
    # Murs périphériques
    grid[0, :] = -1
    grid[-1, :] = -1
    grid[:, 0] = -1
    grid[:, -1] = -1
    
    # Points d'intérêt aux extrémités des rayons
    points_of_interest = []
    for y in range(5, height-5, 8):
        points_of_interest.append((2, y+1))
        points_of_interest.append((width-3, y+1))
    
    # Entrée/sortie
    grid[height//2, 0] = 0
    points_of_interest.append((1, height//2))
    
    return grid, points_of_interest


def load_from_image(image_path, width, height, threshold=128):
    """Charge une grille depuis une image"""
    try:
        from PIL import Image
        
        img = Image.open(image_path).convert('L')
        img = img.resize((width, height))
        img_array = np.array(img)
        
        # Convertir en grille (seuil pour noir/blanc)
        grid = np.where(img_array < threshold, -1, 0).astype(np.int8)
        
        return grid, []
        
    except ImportError:
        print("Erreur: PIL/Pillow n'est pas installé. Installez-le avec: pip install Pillow")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors du chargement de l'image: {e}")
        sys.exit(1)


def save_hdf5(grid, points_of_interest, hedge_size, filename):
    """Sauvegarde la grille en HDF5"""
    try:
        with h5py.File(filename, 'w') as f:
            # Dataset matrix
            matrix_ds = f.create_dataset('matrix', data=grid, dtype='int8')
            matrix_ds.attrs['hedge_size'] = hedge_size
            
            # Dataset points_of_interest
            if points_of_interest:
                poi_array = np.array(points_of_interest, dtype='int16')
                f.create_dataset('points_of_interest', data=poi_array, dtype='int16')
            
        print(f"Grille sauvegardée: {filename}")
        print(f"Dimensions: {grid.shape[1]}x{grid.shape[0]}")
        print(f"Taille cellule: {hedge_size}")
        print(f"Points d'intérêt: {len(points_of_interest)}")
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        sys.exit(1)


def save_json(grid, points_of_interest, hedge_size, filename):
    """Sauvegarde la grille en JSON"""
    try:
        data = {
            'matrix': grid.tolist(),
            'hedge_size': hedge_size,
            'points_of_interest': points_of_interest,
            'width': grid.shape[1],
            'height': grid.shape[0]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Grille sauvegardée: {filename}")
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        sys.exit(1)


def print_grid_info(grid, points_of_interest, hedge_size):
    """Affiche les informations de la grille"""
    obstacles = np.sum(grid == -1)
    free_cells = np.sum(grid == 0)
    total_cells = grid.shape[0] * grid.shape[1]
    
    print(f"\n=== Informations de la grille ===")
    print(f"Dimensions: {grid.shape[1]}x{grid.shape[0]} ({total_cells} cellules)")
    print(f"Taille cellule: {hedge_size}")
    print(f"Cellules libres: {free_cells} ({free_cells/total_cells*100:.1f}%)")
    print(f"Obstacles: {obstacles} ({obstacles/total_cells*100:.1f}%)")
    print(f"Points d'intérêt: {len(points_of_interest)}")
    
    if points_of_interest:
        print("\nPoints d'intérêt:")
        for i, (x, y) in enumerate(points_of_interest):
            print(f"  POI {i+1}: ({x}, {y})")


def main():
    parser = argparse.ArgumentParser(description="Générateur de grilles HDF5 pour JPS/TSP")
    
    parser.add_argument('-w', '--width', type=int, default=50, help="Largeur de la grille (défaut: 50)")
    parser.add_argument('--height', type=int, default=50, help="Hauteur de la grille (défaut: 50)")
    parser.add_argument('-s', '--hedge-size', type=float, default=1.0, help="Taille des cellules (défaut: 1.0)")
    parser.add_argument('-o', '--output', required=True, help="Fichier de sortie (.h5 ou .json)")
    
    # Types de grilles
    grid_group = parser.add_mutually_exclusive_group(required=True)
    grid_group.add_argument('--empty', action='store_true', help="Grille vide")
    grid_group.add_argument('--random', nargs='?', const=0.2, type=float, metavar='RATIO', 
                          help="Grille aléatoire (ratio d'obstacles, défaut: 0.2)")
    grid_group.add_argument('--maze', action='store_true', help="Grille labyrinthe")
    grid_group.add_argument('--store', action='store_true', help="Layout de magasin")
    grid_group.add_argument('--image', type=str, metavar='PATH', help="Charger depuis une image")
    
    # Options pour la grille aléatoire
    parser.add_argument('--num-poi', type=int, default=5, help="Nombre de points d'intérêt (défaut: 5)")
    parser.add_argument('--threshold', type=int, default=128, help="Seuil pour conversion image (défaut: 128)")
    
    # Options d'affichage
    parser.add_argument('--info', action='store_true', help="Afficher les informations de la grille")
    parser.add_argument('--preview', action='store_true', help="Afficher un aperçu en ASCII")
    
    args = parser.parse_args()
    
    # Créer la grille selon le type choisi
    if args.empty:
        grid, poi = create_empty_grid(args.width, args.height, args.hedge_size)
    elif args.random is not None:
        grid, poi = create_random_grid(args.width, args.height, args.hedge_size, 
                                     args.random, args.num_poi)
    elif args.maze:
        grid, poi = create_maze_grid(args.width, args.height, args.hedge_size)
    elif args.store:
        grid, poi = create_store_layout(args.width, args.height, args.hedge_size)
    elif args.image:
        grid, poi = load_from_image(args.image, args.width, args.height, args.threshold)
    
    # Afficher les informations si demandé
    if args.info:
        print_grid_info(grid, poi, args.hedge_size)
    
    # Afficher un aperçu ASCII si demandé
    if args.preview:
        print("\n=== Aperçu de la grille ===")
        preview_grid = grid.copy()
        for x, y in poi:
            if 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]:
                preview_grid[y, x] = 1
        
        char_map = {-1: '█', 0: '·', 1: '●'}
        for row in preview_grid:
            print(''.join(char_map.get(cell, '?') for cell in row))
        print("Légende: █ = obstacle, · = libre, ● = point d'intérêt\n")
    
    # Sauvegarder
    if args.output.endswith(('.h5', '.hdf5')):
        save_hdf5(grid, poi, args.hedge_size, args.output)
    elif args.output.endswith('.json'):
        save_json(grid, poi, args.hedge_size, args.output)
    else:
        print("Erreur: Format de fichier non supporté. Utilisez .h5, .hdf5 ou .json")
        sys.exit(1)


if __name__ == "__main__":
    main()