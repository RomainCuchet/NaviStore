#!/usr/bin/env python3
"""
Démonstration du module JPS/TSP
Test du module Python compilé avec des grilles générées
"""

import sys
import os
import numpy as np

# Ajouter le chemin du module
sys.path.insert(0, '/home/romain/Desktop/NaviStore/server/api_products/jsp_tsp_optimized/python_bridge')

try:
    import jps_tsp
    print("✓ Module jps_tsp importé avec succès!")
except ImportError as e:
    print(f"✗ Impossible d'importer le module jps_tsp: {e}")
    print("Assurez-vous que le module a été compilé avec 'make python'")
    sys.exit(1)


def test_basic_functionality():
    """Test basique du module"""
    print("\n=== Test basique du module ===")
    
    try:
        # Test de création d'un objet JTSolver
        print("Test de création d'un solver...")
        
        # Créer une grille simple pour le test
        from grid_generator_cli import create_random_grid, save_hdf5
        
        grid, poi = create_random_grid(20, 20, 1.0, 0.1, 3)
        test_file = "/tmp/test_grid.h5"
        save_hdf5(grid, poi, 1.0, test_file)
        
        print(f"Grille de test créée: {test_file}")
        print(f"Dimensions: {grid.shape}")
        print(f"Points d'intérêt: {len(poi)}")
        
        # Tenter de créer le solver
        try:
            solver = jps_tsp.JTSolver(test_file)
            print("✓ JTSolver créé avec succès!")
            
            # Tester les méthodes disponibles
            print("\nMéthodes disponibles:")
            for attr in dir(solver):
                if not attr.startswith('_'):
                    print(f"  - {attr}")
            
        except Exception as e:
            print(f"✗ Erreur lors de la création du solver: {e}")
            return False
        
        # Nettoyer
        if os.path.exists(test_file):
            os.remove(test_file)
            
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans le test: {e}")
        return False


def create_demo_grids():
    """Crée des grilles de démonstration"""
    print("\n=== Création de grilles de démonstration ===")
    
    from grid_generator_cli import create_empty_grid, create_random_grid, create_store_layout, save_hdf5
    
    grids_dir = "/home/romain/Desktop/NaviStore/server/api_products/jsp_tsp_optimized/demo_grids"
    os.makedirs(grids_dir, exist_ok=True)
    
    demos = [
        ("empty_10x10", lambda: create_empty_grid(10, 10, 1.0)),
        ("random_20x20", lambda: create_random_grid(20, 20, 1.0, 0.2, 4)),
        ("store_30x20", lambda: create_store_layout(30, 20, 1.0)),
    ]
    
    created_files = []
    
    for name, generator in demos:
        try:
            grid, poi = generator()
            filename = os.path.join(grids_dir, f"{name}.h5")
            save_hdf5(grid, poi, 1.0, filename)
            created_files.append(filename)
            print(f"✓ {name}: {grid.shape[1]}x{grid.shape[0]}, {len(poi)} POI")
        except Exception as e:
            print(f"✗ Erreur pour {name}: {e}")
    
    return created_files


def test_with_demo_grids(grid_files):
    """Test le module avec les grilles de démonstration"""
    print("\n=== Test avec grilles de démonstration ===")
    
    for grid_file in grid_files:
        print(f"\nTest avec {os.path.basename(grid_file)}:")
        
        try:
            solver = jps_tsp.JTSolver(grid_file)
            print(f"  ✓ Solver créé")
            
            # Ici on pourrait tester d'autres méthodes du solver
            # une fois qu'elles seront implémentées dans le bridge
            
        except Exception as e:
            print(f"  ✗ Erreur: {e}")


def interactive_demo():
    """Démonstration interactive"""
    print("\n=== Démonstration interactive ===")
    print("Cette démonstration vous permet de tester le module avec vos propres grilles.")
    
    while True:
        print("\nOptions:")
        print("1. Créer une grille aléatoire et la tester")
        print("2. Tester avec une grille existante")
        print("3. Afficher l'aide du module")
        print("0. Quitter")
        
        choice = input("\nVotre choix: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            create_and_test_random()
        elif choice == "2":
            test_existing_grid()
        elif choice == "3":
            show_module_help()
        else:
            print("Choix invalide!")


def create_and_test_random():
    """Crée et teste une grille aléatoire"""
    try:
        width = int(input("Largeur (défaut 25): ") or "25")
        height = int(input("Hauteur (défaut 25): ") or "25")
        ratio = float(input("Ratio d'obstacles (défaut 0.15): ") or "0.15")
        num_poi = int(input("Nombre de POI (défaut 5): ") or "5")
        
        from grid_generator_cli import create_random_grid, save_hdf5
        
        grid, poi = create_random_grid(width, height, 1.0, ratio, num_poi)
        test_file = "/tmp/interactive_test.h5"
        save_hdf5(grid, poi, 1.0, test_file)
        
        print(f"\nGrille créée: {grid.shape[1]}x{grid.shape[0]}")
        print(f"Obstacles: {np.sum(grid == -1)} ({np.sum(grid == -1)/grid.size*100:.1f}%)")
        print(f"Points d'intérêt: {len(poi)}")
        
        # Afficher un aperçu
        if width <= 50 and height <= 30:
            print("\nAperçu:")
            display_grid = grid.copy()
            for x, y in poi:
                display_grid[y, x] = 1
            
            char_map = {-1: '█', 0: '·', 1: '●'}
            for row in display_grid:
                print(''.join(char_map.get(cell, '?') for cell in row))
        
        # Tester avec le module
        try:
            solver = jps_tsp.JTSolver(test_file)
            print("\n✓ Module testé avec succès!")
        except Exception as e:
            print(f"\n✗ Erreur lors du test: {e}")
        
        # Nettoyer
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except KeyboardInterrupt:
        print("\nAnnulé.")
    except Exception as e:
        print(f"Erreur: {e}")


def test_existing_grid():
    """Teste avec une grille existante"""
    filename = input("Chemin vers le fichier .h5: ").strip()
    
    if not os.path.exists(filename):
        print("Fichier introuvable!")
        return
    
    try:
        solver = jps_tsp.JTSolver(filename)
        print("✓ Grille chargée et testée avec succès!")
    except Exception as e:
        print(f"✗ Erreur: {e}")


def show_module_help():
    """Affiche l'aide du module"""
    print("\n=== Aide du module jps_tsp ===")
    print("Module Python pour la planification de chemins avec JPS et TSP")
    print("\nClasses disponibles:")
    
    for name in dir(jps_tsp):
        if not name.startswith('_'):
            obj = getattr(jps_tsp, name)
            if hasattr(obj, '__doc__') and obj.__doc__:
                print(f"\n{name}:")
                print(f"  {obj.__doc__}")
            else:
                print(f"\n{name}: {type(obj)}")


def main():
    """Point d'entrée principal"""
    print("=== Démonstration du module JPS/TSP ===")
    print("Ce script teste le module Python compilé pour la planification de chemins.")
    
    # Test basique
    if not test_basic_functionality():
        print("\n✗ Échec du test basique. Vérifiez la compilation du module.")
        sys.exit(1)
    
    # Créer des grilles de démonstration
    demo_files = create_demo_grids()
    
    # Tester avec les grilles de démonstration
    if demo_files:
        test_with_demo_grids(demo_files)
    
    # Mode interactif
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print("\n\nDémonstration terminée.")
    
    print("\n=== Fin de la démonstration ===")
    print("Les grilles de démonstration sont disponibles dans:")
    print("/home/romain/Desktop/NaviStore/server/api_products/jsp_tsp_optimized/demo_grids/")


if __name__ == "__main__":
    main()