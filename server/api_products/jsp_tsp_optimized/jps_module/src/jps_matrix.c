#include <math.h>
#include <stdlib.h>
#include "../include/jps.h"

JPSResult *jps_compute_all_paths(const Grid *grid, float euclidean_threshold,
                                 const char *cache_path)
{
    JPSResult *result = jps_result_create(grid->poi_count);
    result->grid_hash = compute_grid_hash(grid);

    // Tentative de chargement du cache
    if (cache_path && jps_cache_load(result, cache_path, grid))
    {
        return result;
    }

    // Calcul des paires avec seuil euclidien
    for (uint32_t i = 0; i < grid->poi_count; i++)
    {
        for (uint32_t j = i + 1; j < grid->poi_count; j++)
        {
            Point a = grid->points_of_interest[i];
            Point b = grid->points_of_interest[j];

            // Application du seuil euclidien
            float euclidean_dist = euclidean_distance(a, b);
            if (euclidean_dist > euclidean_threshold)
            {
                continue;
            }

            // Calcul du chemin
            Path *path = jps_find_path_between(grid, a, b);
            if (path)
            {
                uint32_t idx = i * grid->poi_count + j;
                uint32_t idx_sym = j * grid->poi_count + i;

                result->distance_matrix.data[idx] = path->total_cost;
                result->distance_matrix.data[idx_sym] = path->total_cost;
                result->path_matrix[idx] = path;
                result->path_matrix[idx_sym] = path; // Même objet pour la symétrie
            }
        }

        // Diagonale (distance 0, chemin trivial)
        uint32_t idx = i * grid->poi_count + i;
        result->distance_matrix.data[idx] = 0.0f;

        // Chemin trivial: point unique
        result->path_matrix[idx] = malloc(sizeof(Path));
        result->path_matrix[idx]->points = malloc(sizeof(Point));
        result->path_matrix[idx]->points[0] = grid->points_of_interest[i];
        result->path_matrix[idx]->point_count = 1;
        result->path_matrix[idx]->total_cost = 0;
    }

    // Sauvegarde du cache si demandé
    if (cache_path)
    {
        jps_cache_save(result, cache_path);
    }

    return result;
}
