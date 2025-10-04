#!/usr/bin/env python3
"""
Lanceur pour le Simulateur A*.

Script simple pour démarrer le simulateur avec différentes options.
"""

import os
import sys


def main():
    """Lance le simulateur A*."""
    print("🎯 Lancement du Simulateur A* NaviStore")
    print("=" * 50)

    # Vérifier que le fichier existe
    simulator_path = os.path.join(os.path.dirname(__file__), "astar_simulator.py")

    if not os.path.exists(simulator_path):
        print(f"❌ Simulateur non trouvé: {simulator_path}")
        return

    print("🚀 Démarrage du simulateur...")
    print("   Interface graphique Pygame")
    print("   Support grilles H5")
    print("   Visualisation A* temps réel")
    print("")
    print("📋 Contrôles rapides:")
    print("   • Clic: Sélectionner départ/arrivée")
    print("   • ESPACE: Étape suivante")
    print("   • A: Mode auto/manuel")
    print("   • R: Reset")
    print("   • ESC: Quitter")
    print("")

    # Lancer le simulateur
    try:
        os.system(f'python "{simulator_path}"')
    except KeyboardInterrupt:
        print("\n🛑 Simulateur interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors du lancement: {e}")


if __name__ == "__main__":
    main()
