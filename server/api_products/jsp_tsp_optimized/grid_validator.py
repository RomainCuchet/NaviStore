#!/usr/bin/env python3
"""
Vérificateur de grilles HDF5
Script pour valider et analyser les grilles générées
"""

import h5py
import numpy as np
import argparse
import json
import sys


def validate_hdf5_grid(filename):
    """Valide une grille HDF5"""
    try:
        with h5py.File(filename, 'r') as f:
            print(f"=== Validation de {filename} ===\n")
            
            # Vérifier la structure
            required_datasets = ['matrix']
            optional_datasets = ['points_of_interest']
            
            print("Structure du fichier:")
            for dataset in required_datasets:
                if dataset in f:
                    print(f"  ✓ {dataset}")
                else:
                    print(f"  ✗ {dataset} (REQUIS)")
                    return False
            
            for dataset in optional_datasets:
                if dataset in f:
                    print(f"  ✓ {dataset}")
                else:
                    print(f"  - {dataset} (optionnel)")
            
            # Analyser la matrice
            matrix = f['matrix']
            print(f"\nMatrice:")
            print(f"  Dimensions: {matrix.shape}")
            print(f"  Type: {matrix.dtype}")
            
            # Vérifier les attributs
            print(f"\nAttributs de la matrice:")
            for attr_name in matrix.attrs:
                attr_value = matrix.attrs[attr_name]
                print(f"  {attr_name}: {attr_value}")
            
            if 'hedge_size' not in matrix.attrs:
                print("  ⚠️  hedge_size manquant (utilisera 1.0 par défaut)")
            
            # Analyser les données
            grid_data = matrix[:]
            unique_values = np.unique(grid_data)
            print(f"\nValeurs dans la grille: {unique_values}")
            
            # Statistiques
            total_cells = grid_data.size
            obstacles = np.sum(grid_data == -1)
            free_cells = np.sum(grid_data == 0)
            poi_cells = np.sum(grid_data == 1)
            other_cells = total_cells - obstacles - free_cells - poi_cells
            
            print(f"\nStatistiques:")
            print(f"  Total cellules: {total_cells}")
            print(f"  Cellules libres (0): {free_cells} ({free_cells/total_cells*100:.1f}%)")
            print(f"  Obstacles (-1): {obstacles} ({obstacles/total_cells*100:.1f}%)")
            if poi_cells > 0:
                print(f"  POI dans matrice (1): {poi_cells} ({poi_cells/total_cells*100:.1f}%)")
            if other_cells > 0:
                print(f"  Autres valeurs: {other_cells}")
            
            # Analyser les points d'intérêt
            if 'points_of_interest' in f:
                poi_data = f['points_of_interest'][:]
                print(f"\nPoints d'intérêt:")
                print(f"  Nombre: {poi_data.shape[0]}")
                print(f"  Type: {poi_data.dtype}")
                print(f"  Shape: {poi_data.shape}")
                
                if poi_data.shape[1] != 2:
                    print(f"  ✗ Format incorrect: attendu (N, 2), trouvé {poi_data.shape}")
                    return False
                
                # Vérifier que les POI sont dans les limites
                height, width = matrix.shape
                valid_poi = []
                invalid_poi = []
                
                for i, (x, y) in enumerate(poi_data):
                    if 0 <= x < width and 0 <= y < height:
                        valid_poi.append((x, y))
                        # Vérifier si le POI est sur une cellule libre
                        if grid_data[y, x] != 0 and grid_data[y, x] != 1:
                            print(f"  ⚠️  POI {i+1} ({x}, {y}) n'est pas sur une cellule libre (valeur: {grid_data[y, x]})")
                    else:
                        invalid_poi.append((x, y))
                
                if invalid_poi:
                    print(f"  ✗ POI hors limites: {invalid_poi}")
                    return False
                
                print(f"  ✓ Tous les POI sont valides")
                
                # Afficher les POI
                if len(valid_poi) <= 10:
                    for i, (x, y) in enumerate(valid_poi):
                        print(f"    POI {i+1}: ({x}, {y})")
                else:
                    print(f"    (liste tronquée - {len(valid_poi)} POI au total)")
            
            print(f"\n✓ Grille valide!")
            return True
            
    except Exception as e:
        print(f"✗ Erreur lors de la validation: {e}")
        return False


def analyze_connectivity(filename):
    """Analyse la connectivité de la grille"""
    try:
        with h5py.File(filename, 'r') as f:
            grid = f['matrix'][:]
            
            print(f"\n=== Analyse de connectivité ===")
            
            # Trouver toutes les cellules libres
            free_cells = np.where(grid == 0)
            if len(free_cells[0]) == 0:
                print("Aucune cellule libre trouvée!")
                return
            
            # Algorithme de flood fill pour trouver les composantes connexes
            visited = np.zeros_like(grid, dtype=bool)
            components = []
            
            def flood_fill(start_y, start_x):
                stack = [(start_y, start_x)]
                component = []
                
                while stack:
                    y, x = stack.pop()
                    if (y < 0 or y >= grid.shape[0] or x < 0 or x >= grid.shape[1] or 
                        visited[y, x] or grid[y, x] != 0):
                        continue
                    
                    visited[y, x] = True
                    component.append((x, y))
                    
                    # Ajouter les voisins (4-connectivité)
                    stack.extend([(y-1, x), (y+1, x), (y, x-1), (y, x+1)])
                
                return component
            
            # Trouver toutes les composantes connexes
            for y, x in zip(free_cells[0], free_cells[1]):
                if not visited[y, x]:
                    component = flood_fill(y, x)
                    if component:
                        components.append(component)
            
            print(f"Nombre de composantes connexes: {len(components)}")
            
            if len(components) > 1:
                print("⚠️  Grille fragmentée - certains points ne sont pas accessibles!")
                for i, comp in enumerate(components):
                    print(f"  Composante {i+1}: {len(comp)} cellules")
            else:
                print("✓ Toutes les cellules libres sont connectées")
            
            # Vérifier les POI
            if 'points_of_interest' in f:
                poi_data = f['points_of_interest'][:]
                poi_components = {}
                
                for i, (x, y) in enumerate(poi_data):
                    for comp_idx, comp in enumerate(components):
                        if (x, y) in comp:
                            if comp_idx not in poi_components:
                                poi_components[comp_idx] = []
                            poi_components[comp_idx].append(i+1)
                            break
                
                print(f"\nRépartition des POI par composante:")
                for comp_idx, poi_list in poi_components.items():
                    print(f"  Composante {comp_idx+1}: POI {poi_list}")
                
                if len(poi_components) > 1:
                    print("⚠️  Les POI sont répartis sur plusieurs composantes non connectées!")
            
    except Exception as e:
        print(f"Erreur lors de l'analyse: {e}")


def export_to_ascii(filename, output_file=None):
    """Exporte la grille en ASCII"""
    try:
        with h5py.File(filename, 'r') as f:
            grid = f['matrix'][:]
            
            # Marquer les POI si disponibles
            display_grid = grid.copy()
            if 'points_of_interest' in f:
                poi_data = f['points_of_interest'][:]
                for x, y in poi_data:
                    if 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]:
                        display_grid[y, x] = 1
            
            # Caractères pour l'affichage
            char_map = {-1: '█', 0: '·', 1: '●'}
            
            lines = []
            lines.append(f"# Grille {grid.shape[1]}x{grid.shape[0]}")
            lines.append(f"# Légende: █ = obstacle, · = libre, ● = point d'intérêt")
            lines.append("")
            
            for row in display_grid:
                line = ''.join(char_map.get(cell, '?') for cell in row)
                lines.append(line)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                print(f"Grille exportée vers {output_file}")
            else:
                print('\n'.join(lines))
                
    except Exception as e:
        print(f"Erreur lors de l'export: {e}")


def compare_grids(file1, file2):
    """Compare deux grilles"""
    try:
        with h5py.File(file1, 'r') as f1, h5py.File(file2, 'r') as f2:
            print(f"\n=== Comparaison {file1} vs {file2} ===")
            
            grid1 = f1['matrix'][:]
            grid2 = f2['matrix'][:]
            
            # Dimensions
            if grid1.shape != grid2.shape:
                print(f"✗ Dimensions différentes: {grid1.shape} vs {grid2.shape}")
                return
            
            print(f"✓ Mêmes dimensions: {grid1.shape}")
            
            # Contenu
            differences = np.sum(grid1 != grid2)
            total_cells = grid1.size
            
            if differences == 0:
                print("✓ Grilles identiques")
            else:
                print(f"✗ {differences} cellules différentes ({differences/total_cells*100:.1f}%)")
            
            # POI
            poi1 = set()
            poi2 = set()
            
            if 'points_of_interest' in f1:
                poi1 = set(tuple(poi) for poi in f1['points_of_interest'][:])
            
            if 'points_of_interest' in f2:
                poi2 = set(tuple(poi) for poi in f2['points_of_interest'][:])
            
            common_poi = poi1 & poi2
            only_in_1 = poi1 - poi2
            only_in_2 = poi2 - poi1
            
            print(f"POI communs: {len(common_poi)}")
            if only_in_1:
                print(f"POI uniquement dans {file1}: {list(only_in_1)}")
            if only_in_2:
                print(f"POI uniquement dans {file2}: {list(only_in_2)}")
                
    except Exception as e:
        print(f"Erreur lors de la comparaison: {e}")


def main():
    parser = argparse.ArgumentParser(description="Vérificateur de grilles HDF5")
    
    parser.add_argument('filename', help="Fichier HDF5 à analyser")
    parser.add_argument('--connectivity', action='store_true', help="Analyser la connectivité")
    parser.add_argument('--ascii', nargs='?', const=True, help="Exporter en ASCII (optionnel: fichier de sortie)")
    parser.add_argument('--compare', type=str, help="Comparer avec une autre grille")
    
    args = parser.parse_args()
    
    # Validation de base
    if not validate_hdf5_grid(args.filename):
        sys.exit(1)
    
    # Analyse de connectivité
    if args.connectivity:
        analyze_connectivity(args.filename)
    
    # Export ASCII
    if args.ascii is not None:
        output_file = args.ascii if isinstance(args.ascii, str) else None
        export_to_ascii(args.filename, output_file)
    
    # Comparaison
    if args.compare:
        compare_grids(args.filename, args.compare)


if __name__ == "__main__":
    main()