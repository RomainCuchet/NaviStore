"""
Lanceur pour l'éditeur de grille de magasin.

Script simple pour lancer l'éditeur de grille avec interface Pygame.
"""

import sys
import os

# Ajouter le chemin du serveur au PYTHONPATH
server_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, server_path)

try:
    from tools.grid_editor import main

    if __name__ == "__main__":
        print("Lancement de l'éditeur de grille de magasin...")
        print("Assurez-vous d'avoir installé les dépendances avec 'pip install pygame'")
        main()

except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print("Installez pygame avec: pip install pygame")
    sys.exit(1)
except Exception as e:
    print(f"Erreur: {e}")
    sys.exit(1)
