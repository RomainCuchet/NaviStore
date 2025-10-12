"""
Lanceur pour l'éditeur de grille de magasin.

Script simple pour lancer l'éditeur de grille avec interface Pygame.
"""

import sys
import os

# Ajouter le chemin du serveur au PYTHONPATH
n_path = os.path.dirname(__file__), "..", ".."
server_path = os.path.join(*n_path)
sys.path.insert(0, server_path)

try:
    # Import depuis le dossier local
    from grid_editor import main

    if __name__ == "__main__":
        print("Lancement de l'éditeur de grille de magasin...")
        main()

except ImportError as e:
    print(f"Erreur d'importation: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Erreur: {e}")
    sys.exit(1)
