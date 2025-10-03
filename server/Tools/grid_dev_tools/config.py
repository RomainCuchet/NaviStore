"""
Configuration pour les outils de développement de grille.

Contient les paramètres configurables pour les tests d'API.
"""

# Configuration API
API_CONFIG = {
    "base_url": "http://localhost:8000",
    "api_key": "7nO71v2xVGrkcidbYiM8XIp5IDgfN1C1",  # Remplacez par votre vraie clé API
    "timeout": 30,  # Timeout en secondes pour les requêtes
}

# Configuration visuelle
VISUAL_CONFIG = {
    "cell_size": 15,  # Taille des cellules en pixels
    "poi_count": 15,  # Nombre de POIs à générer
    "window_title": "Testeur d'Optimisation NaviStore",
}

# Configuration d'optimisation
OPTIMIZATION_CONFIG = {
    "distance_threshold": 1000000,  # Seuil de distance en cm
    "max_runtime": 10,  # Temps max d'optimisation en secondes
    "include_return_to_start": True,  # Retourner au point de départ
}


def get_api_key():
    """Retourne la clé API configurée."""
    return API_CONFIG["api_key"]


def get_api_base_url():
    """Retourne l'URL de base de l'API."""
    return API_CONFIG["base_url"]


def update_api_key(new_key: str):
    """Met à jour la clé API."""
    API_CONFIG["api_key"] = new_key
    print(f"✅ Clé API mise à jour: {new_key[:10]}...")


def print_config():
    """Affiche la configuration actuelle."""
    print("📋 Configuration actuelle:")
    print(f"   URL API: {API_CONFIG['base_url']}")
    print(
        f"   Clé API: {API_CONFIG['api_key'][:10]}..."
        if len(API_CONFIG["api_key"]) > 10
        else f"   Clé API: {API_CONFIG['api_key']}"
    )
    print(f"   Nombre POIs: {VISUAL_CONFIG['poi_count']}")
    print(f"   Seuil distance: {OPTIMIZATION_CONFIG['distance_threshold']} cm")


if __name__ == "__main__":
    # Afficher la configuration actuelle
    print_config()

    # Demander une nouvelle clé API si nécessaire
    if API_CONFIG["api_key"] == "your-api-key-here":
        print("\n⚠️ Clé API par défaut détectée!")
        new_key = input(
            "Entrez votre clé API (ou appuyez sur Entrée pour garder celle par défaut): "
        ).strip()
        if new_key:
            update_api_key(new_key)
