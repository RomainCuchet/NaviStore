# Éditeur de Grille de Magasin

Un éditeur graphique avec interface Pygame pour créer et modifier les layouts de magasin utilisés par le système d'optimisation de chemin JPS-TSP.

## Installation

Assurez-vous d'avoir installé les dépendances :

```bash
pip install pygame numpy h5py tkinter
```

Ou installez toutes les dépendances du projet :

```bash
pip install -r requirements.txt
```

## Lancement

### Méthode 1 : Script de lancement
```bash
cd server/tools
python launch_grid_editor.py
```

### Méthode 2 : Direct
```bash
cd server/tools
python grid_editor.py
```

### Méthode 3 : Depuis la racine
```bash
python server/tools/launch_grid_editor.py
```

## Utilisation

### Interface

L'éditeur présente :
- **Grille principale** : Zone d'édition avec cellules colorées
- **Panneau d'informations** : Statistiques et contrôles
- **Boutons** : Actions principales (Nouveau, Ouvrir, Sauver, etc.)

### Contrôles Souris

- **Clic gauche** : Placer zone libre (blanc) - valeur 0
- **Clic droit** : Placer obstacle (noir) - valeur -1
- **Clic milieu** : Placer POI (vert) - valeur 1
- **Glissement** : Dessiner en continu avec l'outil sélectionné

### Raccourcis Clavier

- **S** : Sauvegarder la grille
- **R** : Réinitialiser (annuler modifications)
- **ESC** : Quitter l'éditeur
- **+/-** : Ajuster le zoom (taille des cellules)

### Boutons Interface

- **Nouveau** : Créer une nouvelle grille (dimensions personnalisées)
- **Ouvrir** : Charger une grille depuis un fichier .h5
- **Sauver** : Sauvegarder la grille au format .h5
- **Reset** : Annuler toutes les modifications
- **Taille** : Redimensionner la grille actuelle
- **Quitter** : Fermer l'éditeur

## Types de Cellules

### Zone Libre (0) - Blanc
- Zones navigables pour les clients
- Allées principales et secondaires
- Passages entre rayons

### Obstacle (-1) - Noir
- Rayonnages et étagères
- Murs et cloisons
- Caisses et comptoirs
- Zones interdites

### Point d'Intérêt (1) - Vert
- Emplacements de produits spécifiques
- Zones de collecte importantes
- Points de référence

## Format de Fichier

Les grilles sont sauvegardées au format HDF5 (.h5) avec :

```python
# Structure du fichier
{
    'layout': numpy.array,      # Grille 2D avec valeurs 0, -1, 1
    'edge_length': float        # Taille d'une cellule en centimètres
}
```

### Métadonnées

Un fichier JSON est automatiquement créé avec les métadonnées :

```json
{
    "grid_shape": [hauteur, largeur],
    "edge_length": 100.0,
    "statistics": {
        "navigable": 150,
        "obstacles": 80,
        "pois": 5
    }
}
```

## Exemples Prédéfinis

Générez des exemples de layouts :

```bash
cd server/tools
python create_example_layouts.py
```

Cela crée le dossier `examples/` avec :

### simple_store.h5
- Petit magasin 15x10
- Rayonnages réguliers
- Allées simples
- Cellules de 50cm

### complex_store.h5
- Magasin moyen 25x20
- Zones spécialisées
- Multiple entrées
- Cellules de 75cm

### supermarket.h5
- Grand supermarché 30x40
- Layout réaliste
- Zones fruits/légumes, boucherie, caisses
- Cellules de 100cm

## Intégration avec l'API

Les grilles créées peuvent être directement utilisées avec l'API d'optimisation :

```python
# Upload du layout
with open('mon_magasin.h5', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/path_optimization/upload_layout',
        files={'layout_file': f},
        headers={'X-API-Key': 'your-key'}
    )

# Optimisation de chemin
shopping_list = [
    {"product_id": 1, "location_x": 100, "location_y": 200, "quantity": 1},
    {"product_id": 2, "location_x": 300, "location_y": 400, "quantity": 1}
]

response = requests.post(
    'http://localhost:8000/path_optimization/optimize_shopping_list',
    json={"shopping_list": shopping_list},
    headers={'X-API-Key': 'your-key'}
)
```

## Conseils d'Utilisation

### Création de Layout Réaliste

1. **Commencez par les murs** : Délimitez l'espace avec des obstacles
2. **Ajoutez les grandes structures** : Rayonnages principaux
3. **Créez les allées** : Zones de circulation libres
4. **Définissez les zones spéciales** : Caisses, stockage, services
5. **Placez les POIs** : Emplacements produits si nécessaire

### Bonnes Pratiques

- **Proportions réalistes** : Respectez les dimensions d'un vrai magasin
- **Allées suffisamment larges** : Minimum 1-2 cellules de large
- **Cohérence** : Gardez un style architectural logique
- **Testez la navigation** : Vérifiez que tous les POIs sont accessibles

### Optimisation Performance

- **Taille raisonnable** : Évitez les grilles trop grandes (>100x100)
- **Edge length approprié** : Ajustez selon la précision nécessaire
- **Zones connectées** : Assurez-vous que tous les POIs sont atteignables

## Dépannage

### Erreurs Communes

**"pygame not found"**
```bash
pip install pygame
```

**"h5py not found"**
```bash
pip install h5py
```

**"Grille trop grande"**
- Réduisez les dimensions
- Augmentez edge_length
- Utilisez le zoom pour naviguer

### Problèmes d'Affichage

- **Fenêtre trop petite** : Utilisez +/- pour ajuster le zoom
- **Interface coupée** : Redimensionnez la grille ou la fenêtre
- **Performance lente** : Réduisez la taille de la grille

## Développement

### Architecture du Code

```
grid_editor.py
├── GridEditor           # Classe principale
├── Gestion affichage   # Rendu Pygame
├── Gestion événements  # Souris/clavier
├── Interface utilisateur # Boutons, dialogues
└── Sauvegarde/Chargement # Fichiers HDF5
```

### Extension

L'éditeur peut être étendu pour :
- Support de layers multiples
- Outils de dessin avancés
- Import/export autres formats
- Prévisualisation de chemins
- Mode collaboratif

### Tests

Testez l'éditeur avec différents scenarios :

```bash
# Test création
python grid_editor.py
# Nouveau → 10x10 → Dessiner → Sauver

# Test chargement
python create_example_layouts.py
python grid_editor.py
# Ouvrir → examples/simple_store.h5

# Test API
# Créer grille → Sauver → Tester avec l'API path_optimization
```

L'éditeur de grille est maintenant prêt à utiliser pour créer des layouts de magasin optimisés !