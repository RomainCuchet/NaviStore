#ifndef JPS_H
#define JPS_H

#include "../../common/include/common.h"

#define JPS_CACHE_EXTENSION ".jps"
#define JPS_CACHE_VERSION 3

typedef struct
{
    Path **path_matrix; // Matrice des chemins entre POI
    DistanceMatrix distance_matrix;
    uint32_t poi_count;
    uint64_t grid_hash;
} JPSResult;

// API JPS
JPSResult *jps_result_create(uint32_t poi_count);
JPSResult *jps_compute_all_paths(const Grid *grid, float euclidean_threshold,
                                 const char *cache_path);
bool jps_cache_save(const JPSResult *result, const char *filename);
bool jps_cache_load(JPSResult *result, const char *filename, const Grid *grid);
void jps_free_result(JPSResult *result);

// Fonctions de bas niveau
Path *jps_find_path_between(const Grid *grid, Point start, Point goal);

#endif
