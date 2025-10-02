# Générateur de Grilles HDF5 pour JPS/TSP

Ce projet fournit des outils pour créer, valider et utiliser des grilles HDF5 compatibles avec le système de planification de chemins JPS/TSP.

## Structure des fichiers

- `grid_generator.py` - Interface graphique pour créer des grilles
- `grid_generator_cli.py` - Générateur en ligne de commande
- `grid_validator.py` - Validateur et analyseur de grilles
- `demo.py` - Démonstration du module Python compilé

## Installation des dépendances

```bash
# Dépendances système
sudo apt-get install libhdf5-dev pkg-config python3-dev python3-pip

# Dépendances Python
pip install h5py numpy matplotlib tkinter pillow
```

## Compilation du module C

```bash
# Compiler le module Python
make python

# Vérifier que la compilation a réussi
ls python_bridge/*.so
```

## Format des grilles HDF5

Les grilles utilisent le format HDF5 avec la structure suivante :

### Datasets requis
- `/matrix` : Matrice 2D (hauteur × largeur) de type `int8`
  - `-1` = obstacle (cellule bloquée)
  - `0` = cellule libre (navigable)
  - `1` = point d'intérêt (optionnel, peut être géré séparément)

### Attributs requis
- `hedge_size` : Taille réelle d'une cellule (type `float`, défaut: 1.0)

### Datasets optionnels
- `/points_of_interest` : Tableau 2D (N × 2) de type `int16`
  - Chaque ligne contient les coordonnées (x, y) d'un point d'intérêt
  - Les coordonnées sont en indices de grille (pas en unités réelles)

## Utilisation

### 1. Interface graphique

```bash
python3 grid_generator.py
```

L'interface permet de :
- Créer des grilles vides, aléatoires, ou à partir d'images
- Éditer les grilles en cliquant (obstacles, POI)
- Sauvegarder en HDF5 ou JSON
- Prévisualiser en temps réel

### 2. Ligne de commande

```bash
# Grille vide 50×50
python3 grid_generator_cli.py --empty -w 50 -h 50 -o ma_grille.h5

# Grille aléatoire avec 20% d'obstacles et 5 POI
python3 grid_generator_cli.py --random 0.2 --num-poi 5 -w 30 -h 30 -o grille_random.h5

# Grille labyrinthe
python3 grid_generator_cli.py --maze -w 25 -h 25 -o labyrinthe.h5

# Layout de magasin
python3 grid_generator_cli.py --store -w 40 -h 30 -o magasin.h5

# Depuis une image
python3 grid_generator_cli.py --image plan.png -w 100 -h 80 -o grille_image.h5

# Avec aperçu et informations
python3 grid_generator_cli.py --random 0.15 -w 20 -h 15 --preview --info -o test.h5
```

### 3. Validation des grilles

```bash
# Validation basique
python3 grid_validator.py ma_grille.h5

# Analyse de connectivité
python3 grid_validator.py ma_grille.h5 --connectivity

# Export en ASCII
python3 grid_validator.py ma_grille.h5 --ascii

# Export ASCII vers fichier
python3 grid_validator.py ma_grille.h5 --ascii grille.txt

# Comparaison de deux grilles
python3 grid_validator.py grille1.h5 --compare grille2.h5
```

### 4. Démonstration du module

```bash
# Lancer la démonstration interactive
python3 demo.py
```

## Exemples de grilles

### Grille simple pour tests
```bash
python3 grid_generator_cli.py --empty -w 10 -h 10 -o simple.h5
# Puis ajouter manuellement des POI avec l'interface graphique
```

### Environnement de magasin
```bash
python3 grid_generator_cli.py --store -w 50 -h 30 --info --preview -o magasin.h5
```

### Labyrinthe complexe
```bash
python3 grid_generator_cli.py --maze -w 51 -h 51 --num-poi 8 -o labyrinthe_complexe.h5
```

## Intégration avec le code C

Une fois la grille créée, elle peut être utilisée directement avec le module C :

```c
#include "common/include/h5_loader.h"

// Charger la grille
Grid *grid = jps_load_grid_from_h5("ma_grille.h5");
if (!grid) {
    fprintf(stderr, "Impossible de charger la grille\\n");
    return -1;
}

// Utiliser la grille avec JPS/TSP
// ...

// Libérer la mémoire
jps_free_grid(grid);
```

Ou avec le module Python :

```python
import jps_tsp

# Créer le solver
solver = jps_tsp.JTSolver("ma_grille.h5")

# Utiliser le solver
# (méthodes à implémenter selon les besoins)
```

## Types de grilles prédéfinis

### 1. Grille vide
- Toutes les cellules sont libres
- Aucun obstacle
- POI à ajouter manuellement

### 2. Grille aléatoire
- Distribution aléatoire d'obstacles
- POI placés aléatoirement sur les cellules libres
- Paramètres configurables

### 3. Grille labyrinthe
- Génération automatique de couloirs
- Obstacles formant des murs
- POI aux intersections importantes

### 4. Layout de magasin
- Simulation d'un environnement commercial
- Rayons représentés par des obstacles
- POI aux extrémités des rayons et à l'entrée

## Dépannage

### Erreur de compilation
```bash
# Vérifier les dépendances
pkg-config --exists hdf5
python3-config --includes

# Nettoyer et recompiler
make clean
make python
```

### Erreur d'import Python
```bash
# Vérifier que le module est créé
ls python_bridge/*.so

# Tester l'import
cd python_bridge
python3 -c "import jps_tsp; print('OK')"
```

### Grille invalide
```bash
# Valider la structure
python3 grid_validator.py ma_grille.h5

# Vérifier la connectivité
python3 grid_validator.py ma_grille.h5 --connectivity
```

## Conseils d'utilisation

1. **Taille de grille** : Commencez avec des grilles petites (≤ 50×50) pour les tests
2. **Densité d'obstacles** : 10-30% pour un bon équilibre navigabilité/complexité
3. **Points d'intérêt** : 3-10 POI par grille selon la taille
4. **Validation** : Toujours valider avec `grid_validator.py` avant utilisation
5. **Connectivité** : Vérifiez que tous les POI sont accessibles

## Formats supportés

### Entrée
- Images (PNG, JPG, BMP, TIFF) - via PIL/Pillow
- Grilles HDF5 existantes
- Grilles JSON

### Sortie
- HDF5 (format principal)
- JSON (pour débogage)
- ASCII (pour visualisation)

## Performance

- Grilles jusqu'à 1000×1000 : OK en mémoire
- Grilles plus grandes : considérer le streaming HDF5
- POI illimités (dans les limites de la mémoire)

## Licence

Ce code fait partie du projet NaviStore.