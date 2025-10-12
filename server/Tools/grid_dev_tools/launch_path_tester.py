"""
Lanceur pour le testeur d'optimisation de chemin.

Script pour lancer le testeur d'API avec interface visuelle.
"""

import sys
import os

# Ajouter le chemin du serveur au PYTHONPATH
server_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, server_path)

try:
    from path_optimization_tester import main

    if __name__ == "__main__":
        print("🚀 Lancement du testeur d'optimisation de chemin...")
        print()
        print("INSTRUCTIONS:")
        print("1. Assurez-vous que votre serveur API fonctionne sur localhost:8000")
        print("2. Modifiez la clé API dans le code si nécessaire")
        print("3. Le système va:")
        print("   - Vous demander de choisir un fichier H5")
        print("   - Générer 15 POIs aléatoires")
        print("   - Appeler l'API d'optimisation")
        print("   - Afficher le résultat visuellement")
        print()
        print("Appuyez sur ESC pour quitter la visualisation")
        print()

        main()

except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print("Assurez-vous d'avoir installé les dépendances:")
    print("  pip install pygame requests h5py")
    sys.exit(1)
except Exception as e:
    print(f"Erreur: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
