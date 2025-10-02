#!/usr/bin/env python3
"""
Test du système de hash XXH3 64-bit pour les grilles

Ce script teste que le système de hash génère des noms de fichiers cohérents
et uniques basés sur le contenu de la grille.
"""

import numpy as np
import tempfile
import os
import sys

# Vérifier les dépendances
try:
    import h5py
    import xxhash
except ImportError as e:
    print(f"❌ Dépendance manquante: {e}")
    print("💡 Pour installer les dépendances:")
    print("   pip install h5py xxhash")
    print("   ou activez l'environnement virtuel navistore_server-venv")
    sys.exit(1)


def calculate_layout_hash(grid: np.ndarray, edge_length: float) -> str:
    """Calcule le hash XXH3 64-bit d'une grille (même logique que dans l'éditeur)."""
    # Créer les données comme dans le système d'optimisation
    grid_bytes = grid.astype(np.int8).tobytes()
    edge_length_bytes = np.array([edge_length], dtype=np.float64).tobytes()

    # Combiner les données
    combined_data = grid_bytes + edge_length_bytes

    # Calculer le hash XXH3 64-bit
    hasher = xxhash.xxh3_64()
    hasher.update(combined_data)

    return hasher.hexdigest()


def test_hash_consistency():
    """Test la cohérence du hash pour la même grille."""
    print("🧪 Test de cohérence du hash...")

    # Créer une grille de test
    grid = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, -1, -1, -1, 0],
            [0, 0, 1, 0, 0],
            [0, -1, -1, -1, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.int8,
    )

    edge_length = 100.0

    # Calculer le hash plusieurs fois
    hash1 = calculate_layout_hash(grid, edge_length)
    hash2 = calculate_layout_hash(grid, edge_length)
    hash3 = calculate_layout_hash(grid, edge_length)

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")

    if hash1 == hash2 == hash3:
        print("✅ Cohérence OK: Le même contenu produit le même hash")
    else:
        print("❌ Erreur: Hashes incohérents pour le même contenu!")
        return False

    return True


def test_hash_uniqueness():
    """Test l'unicité du hash pour différentes grilles."""
    print("\n🧪 Test d'unicité du hash...")

    edge_length = 100.0

    # Grille 1
    grid1 = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=np.int8)

    # Grille 2 (différente)
    grid2 = np.array([[0, 0, 0], [0, -1, 0], [0, 0, 0]], dtype=np.int8)

    # Grille 3 (même que 1 mais edge_length différent)
    grid3 = grid1.copy()

    hash1 = calculate_layout_hash(grid1, edge_length)
    hash2 = calculate_layout_hash(grid2, edge_length)
    hash3 = calculate_layout_hash(grid3, 200.0)  # Edge length différent

    print(f"Hash grille 1 (POI au centre): {hash1}")
    print(f"Hash grille 2 (obstacle au centre): {hash2}")
    print(f"Hash grille 3 (comme 1, edge_length=200): {hash3}")

    # Vérifier l'unicité
    hashes = [hash1, hash2, hash3]
    unique_hashes = set(hashes)

    if len(unique_hashes) == 3:
        print("✅ Unicité OK: Contenus différents produisent des hashes différents")
    else:
        print("❌ Erreur: Collision de hash détectée!")
        return False

    return True


def test_file_save_load():
    """Test la sauvegarde et le chargement avec hash."""
    print("\n🧪 Test sauvegarde/chargement avec hash...")

    # Créer une grille de test
    grid = np.array(
        [
            [0, 0, 0, 1, 0],
            [0, -1, 0, 0, 0],
            [0, 0, 0, -1, 0],
            [1, 0, 0, 0, 1],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.int8,
    )

    edge_length = 150.0
    layout_hash = calculate_layout_hash(grid, edge_length)

    print(f"Hash calculé: {layout_hash}")

    # Créer un fichier temporaire avec le nom basé sur le hash
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, f"{layout_hash}.h5")

        # Sauvegarder
        with h5py.File(file_path, "w") as f:
            f.create_dataset("layout", data=grid)
            f.create_dataset("edge_length", data=edge_length)
            f.attrs["layout_hash"] = layout_hash
            f.attrs["created_with"] = "Test Script"

        print(f"Fichier sauvegardé: {os.path.basename(file_path)}")

        # Charger et vérifier
        with h5py.File(file_path, "r") as f:
            loaded_grid = np.array(f["layout"])
            loaded_edge_length = float(f["edge_length"][()])
            stored_hash = f.attrs.get("layout_hash", "")

        # Recalculer le hash du contenu chargé
        recalculated_hash = calculate_layout_hash(loaded_grid, loaded_edge_length)

        print(f"Hash stocké: {stored_hash}")
        print(f"Hash recalculé: {recalculated_hash}")

        # Vérifications
        if np.array_equal(grid, loaded_grid):
            print("✅ Grille correctement sauvegardée/chargée")
        else:
            print("❌ Erreur: Grille corrompue!")
            return False

        if abs(edge_length - loaded_edge_length) < 1e-9:
            print("✅ Edge length correctement sauvegardé/chargé")
        else:
            print("❌ Erreur: Edge length corrompu!")
            return False

        if layout_hash == stored_hash == recalculated_hash:
            print("✅ Hash cohérent dans tout le processus")
        else:
            print("❌ Erreur: Incohérence de hash!")
            return False

    return True


def test_hash_format():
    """Test le format du hash généré."""
    print("\n🧪 Test du format du hash...")

    grid = np.zeros((10, 10), dtype=np.int8)
    edge_length = 100.0
    layout_hash = calculate_layout_hash(grid, edge_length)

    print(f"Hash généré: {layout_hash}")
    print(f"Longueur: {len(layout_hash)} caractères")

    # XXH3 64-bit produit un hash de 16 caractères hexadécimaux
    if len(layout_hash) == 16:
        print("✅ Longueur correcte (16 caractères)")
    else:
        print(f"❌ Erreur: Longueur incorrecte (attendu: 16, reçu: {len(layout_hash)})")
        return False

    # Vérifier que c'est bien hexadécimal
    try:
        int(layout_hash, 16)
        print("✅ Format hexadécimal valide")
    except ValueError:
        print("❌ Erreur: Format hexadécimal invalide!")
        return False

    return True


def main():
    """Exécute tous les tests."""
    print("🚀 Test du système de hash XXH3 64-bit pour les grilles\n")

    tests = [
        test_hash_consistency,
        test_hash_uniqueness,
        test_file_save_load,
        test_hash_format,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("❌ Test échoué!")
        except Exception as e:
            print(f"❌ Erreur durant le test: {e}")

    print(f"\n📊 Résultats: {passed}/{total} tests réussis")

    if passed == total:
        print(
            "🎉 Tous les tests sont passés! Le système de hash fonctionne correctement."
        )
        return 0
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez l'implémentation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
