#!/usr/bin/env python3
"""
Test spécifique pour vérifier que la sérialisation JSON fonctionne correctement
avec les types NumPy dans le grid editor.
"""

import numpy as np
import json
import tempfile
import os


def convert_numpy_types(obj):
    """Convertit les types NumPy en types Python natifs."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


def test_json_serialization():
    """Test la sérialisation JSON avec des types NumPy."""
    print("🧪 Test de sérialisation JSON avec types NumPy...")

    # Simuler les données du grid editor
    grid = np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]], dtype=np.int8)

    # Simuler les statistiques comme dans _update_stats
    unique, counts = np.unique(grid, return_counts=True)
    stats_dict = dict(zip(unique, counts))

    # Version originale (problématique)
    stats_problematic = {
        "navigable": stats_dict.get(0, 0),  # NumPy int64
        "obstacles": stats_dict.get(-1, 0),  # NumPy int64
        "pois": stats_dict.get(1, 0),  # NumPy int64
    }

    # Version corrigée
    stats_fixed = {
        "navigable": int(stats_dict.get(0, 0)),
        "obstacles": int(stats_dict.get(-1, 0)),
        "pois": int(stats_dict.get(1, 0)),
    }

    edge_length = np.float64(100.0)  # NumPy float64

    # Métadonnées problématiques
    metadata_problematic = {
        "grid_shape": grid.shape,  # tuple avec NumPy int64
        "edge_length": edge_length,  # NumPy float64
        "statistics": stats_problematic,  # dict avec NumPy int64
    }

    # Métadonnées corrigées
    metadata_fixed = {
        "grid_shape": [int(grid.shape[0]), int(grid.shape[1])],
        "edge_length": float(edge_length),
        "statistics": convert_numpy_types(stats_fixed),
    }

    # Test 1: Version problématique (devrait échouer)
    print("Test version problématique...")
    try:
        json.dumps(metadata_problematic)
        print("❌ Erreur: La sérialisation problématique n'a pas échoué!")
        return False
    except TypeError as e:
        print(f"✅ Erreur attendue capturée: {e}")

    # Test 2: Version corrigée (devrait réussir)
    print("Test version corrigée...")
    try:
        json_str = json.dumps(metadata_fixed, indent=2)
        print("✅ Sérialisation JSON réussie")

        # Vérifier qu'on peut désérialiser
        parsed = json.loads(json_str)
        print("✅ Désérialisation JSON réussie")

        # Vérifier les types
        assert isinstance(parsed["grid_shape"], list)
        assert isinstance(parsed["grid_shape"][0], int)
        assert isinstance(parsed["edge_length"], float)
        assert isinstance(parsed["statistics"]["navigable"], int)
        print("✅ Types corrects après désérialisation")

    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

    # Test 3: Sauvegarde et chargement fichier
    print("Test sauvegarde/chargement fichier...")
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(metadata_fixed, f, indent=2)
            temp_file = f.name

        with open(temp_file, "r") as f:
            loaded_metadata = json.load(f)

        os.unlink(temp_file)

        # Vérifier que les données sont identiques
        assert loaded_metadata["grid_shape"] == [3, 3]
        assert abs(loaded_metadata["edge_length"] - 100.0) < 1e-9
        assert loaded_metadata["statistics"]["navigable"] == 5
        assert loaded_metadata["statistics"]["obstacles"] == 1
        assert loaded_metadata["statistics"]["pois"] == 2

        print("✅ Sauvegarde/chargement fichier réussi")

    except Exception as e:
        print(f"❌ Erreur fichier: {e}")
        return False

    return True


def main():
    """Test principal."""
    print("🚀 Test de sérialisation JSON pour Grid Editor\n")

    if test_json_serialization():
        print("\n🎉 Tous les tests de sérialisation sont passés!")
        return 0
    else:
        print("\n❌ Des tests ont échoué!")
        return 1


if __name__ == "__main__":
    exit(main())
