# Grid Development Tools

Outils de développement pour tester l'éditeur de grille et l'API d'optimisation de chemin.

## 📁 Fichiers

### Scripts principaux
- `path_optimization_tester.py` - Testeur d'optimisation avec visualisation
- `launch_path_tester.py` - Lanceur pour le testeur d'optimisation
- `grid_editor.py` - Éditeur de grille interactif
- `launch_grid_editor.py` - Lanceur pour l'éditeur de grille

### Configuration
- `config.py` - Configuration des paramètres API et visuels

## 🚀 Utilisation

### 1. Testeur d'Optimisation de Chemin

```bash
cd server/tools/grid_dev_tools
python launch_path_tester.py
```

**Fonctionnalités :**
- ✅ Choix de fichier H5 via navigateur
- ✅ Génération automatique de 15 POIs aléatoires
- ✅ Appel API `/upload_layout` et `/optimize_path`
- ✅ Visualisation du chemin optimal sur la grille
- ✅ Interface Pygame interactive

**Prérequis :**
1. Serveur API démarré sur `localhost:8000`
2. Clé API valide configurée dans `config.py`
3. Fichiers H5 de grilles disponibles

### 2. Éditeur de Grille

```bash
cd server/tools/grid_dev_tools
python launch_grid_editor.py
```

**Fonctionnalités :**
- ✅ Création/édition de grilles
- ✅ Mode coordonnées pour inspection
- ✅ Sauvegarde avec hash XXH3 64-bit
- ✅ Compatible avec l'API d'optimisation

## ⚙️ Configuration

### Configurer la clé API

```python
# Méthode 1: Modifier config.py
API_CONFIG["api_key"] = "votre-vraie-cle-api"

# Méthode 2: Exécuter le configurateur
python config.py
```

### Paramètres d'optimisation

```python
OPTIMIZATION_CONFIG = {
    "distance_threshold": 500.0,  # Seuil de distance en cm
    "max_runtime": 30,           # Temps max en secondes
    "include_return_to_start": True,  # Retour au début
}
```

### Paramètres visuels

```python
VISUAL_CONFIG = {
    "cell_size": 15,      # Taille cellules en pixels
    "poi_count": 15,      # Nombre de POIs à générer
}
```

## 🎯 Workflow de Test Complet

1. **Préparer l'environnement**
   ```bash
   # Démarrer le serveur API
   cd server/api_navimall
   python main.py
   
   # Dans un autre terminal
   cd server/tools/grid_dev_tools
   ```

2. **Configurer la clé API**
   ```bash
   python config.py
   ```

3. **Tester l'optimisation**
   ```bash
   python launch_path_tester.py
   ```

4. **Étapes automatiques :**
   - Choisir fichier H5 (ex: `assets/layout_examples/supermarket.h5`)
   - Le système génère 15 POIs aléatoires
   - Upload de la grille via API
   - Calcul du chemin optimal
   - Affichage visuel du résultat

## 🎨 Légende Visuelle

- **Blanc** : Zone libre (navigable)
- **Noir** : Obstacle
- **Rouge** : Point d'intérêt (POI)
- **Vert** : Chemin optimal calculé
- **Vert foncé** : POI sur le chemin optimal

## 🔧 Dépannage

### Erreurs communes

**"No module named 'server'"**
```bash
# Vérifiez que vous êtes dans le bon répertoire
cd server/tools/grid_dev_tools
```

**"Connection refused"**
```bash
# Vérifiez que le serveur API fonctionne
curl http://localhost:8000/docs
```

**"Invalid API key"**
```bash
# Configurez votre clé API
python config.py
```

### Tests de validation

```bash
# Test de la configuration
python config.py

# Test d'import
python -c "from path_optimization_tester import main; print('OK')"
```

## 📊 Résultats de Test

Le testeur affiche :
- Distance totale du chemin optimal
- Temps de calcul de l'optimisation
- Ordre de visite des POIs
- Visualisation interactive du résultat

## 🔄 Intégration Continue

Ces outils permettent de :
- Valider l'API d'optimisation avec des données réelles
- Tester différentes configurations de grilles
- Vérifier la cohérence entre éditeur et API
- Déboguer visuellement les algorithmes de pathfinding

## 📝 Notes de Développement

- Les coordonnées `(0,0)` correspondent bien à la cellule `[0,0]` de la matrice
- Le format H5 est compatible entre l'éditeur et l'API
- Les hash XXH3 64-bit assurent l'unicité des fichiers
- La visualisation Pygame permet le débogage interactif