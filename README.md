## Elastic Search
Elastic Search is a powerful distributed search engine that perfectly suits our project's needs for several reasons:

1. **Full-Text Search Optimization**: We leverage Elastic Search for efficient full-text search across product titles, providing fast and relevant results.

2. **Document-Based Storage**: Products are indexed using their IDs as document identifiers (_id), enabling optimized multi-get (mget) operations for quick retrievals.

3. **Advanced Filtering**: The engine supports complex search parameters as filters without significant performance impact, allowing refined search results.

4. **Scalability**: Built for distributed systems, it can handle growing product catalogs efficiently.

## Implementation Notes
- To delete index in developer mode: `Invoke-RestMethod -Method Delete -Uri "http://localhost:9200/products"`

## Setup during developpement
- Launch docker desktop
- run from root: `docker compose up`
- run in flutter_app_navistore: `flutter run`

## JPS-TSP Optimized Path Planning

Un système complet de planification de chemin optimal combinant Jump Point Search (JPS) et le problème du voyageur de commerce (TSP) avec LKH.

### 🚀 Features

- **JPS optimisé** avec cache persistant
- **Résolution TSP** avec LKH (fallback: nearest neighbor)
- **Validation** des points d'intérêt et collisions
- **Support HDF5** pour les données d'entrée
- **Interface Python** pour intégration facile

### 📦 Installation

#### Dépendances système
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev
sudo apt-get install libhdf5-dev  # Optionnel pour HDF5

# Installation LKH (optionnel)
wget http://webhotel4.ruc.dk/~keld/research/LKH-3/LKH-2.0.9.tgz
tar xzf LKH-2.0.9.tgz
cd LKH-2.0.9
make
sudo cp LKH /usr/local/bin/