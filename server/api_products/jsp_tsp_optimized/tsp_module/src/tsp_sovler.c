#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/tsp.h"

// Algorithme TSP - Nearest Neighbor (fallback si LKH non disponible)
static uint32_t *solve_tsp_nearest_neighbor(const DistanceMatrix *matrix,
                                            uint32_t poi_count, float *total_distance)
{
    uint32_t *tour = malloc((poi_count + 1) * sizeof(uint32_t));
    bool *visited = calloc(poi_count, sizeof(bool));

    tour[0] = 0; // Commence au premier point
    visited[0] = true;
    *total_distance = 0.0f;

    for (uint32_t i = 1; i < poi_count; i++)
    {
        uint32_t current = tour[i - 1];
        uint32_t next = 0;
        float min_dist = INFINITY;

        // Trouve le point non visité le plus proche
        for (uint32_t j = 0; j < poi_count; j++)
        {
            if (!visited[j])
            {
                float dist = matrix->data[current * poi_count + j];
                if (dist < min_dist)
                {
                    min_dist = dist;
                    next = j;
                }
            }
        }

        tour[i] = next;
        visited[next] = true;
        *total_distance += min_dist;
    }

    // Retour au point de départ
    *total_distance += matrix->data[tour[poi_count - 1] * poi_count + 0];
    tour[poi_count] = 0;

    free(visited);
    return tour;
}

TSPResult *tsp_solve_optimal_tour(const DistanceMatrix *matrix,
                                  const Path **path_matrix,
                                  uint32_t poi_count)
{
    TSPResult *result = malloc(sizeof(TSPResult));

    // Résolution TSP avec LKH ou fallback
    result->tour = malloc((poi_count + 1) * sizeof(uint32_t));
    result->tour_length = poi_count + 1;

    if (!lkh_solve_tsp(matrix, result->tour, &result->total_distance))
    {
        // Fallback vers nearest neighbor
        printf("LKH non disponible, utilisation de nearest neighbor\\n");
        free(result->tour);
        result->tour = solve_tsp_nearest_neighbor(matrix, poi_count, &result->total_distance);
    }

    // Reconstruction du chemin complet
    result->full_path = tsp_reconstruct_full_path(result->tour, result->tour_length,
                                                  path_matrix, poi_count);

    return result;
}

Path *tsp_reconstruct_full_path(const uint32_t *tour, uint32_t tour_length,
                                const Path **path_matrix, uint32_t poi_count)
{
    if (tour_length < 2)
        return NULL;

    // Calcul de la taille totale
    uint32_t total_points = 0;
    for (uint32_t i = 0; i < tour_length - 1; i++)
    {
        uint32_t from = tour[i];
        uint32_t to = tour[i + 1];
        const Path *segment = path_matrix[from * poi_count + to];
        if (segment)
        {
            total_points += segment->point_count - (i > 0 ? 1 : 0);
        }
    }

    // Allocation
    Path *full_path = malloc(sizeof(Path));
    full_path->points = malloc(total_points * sizeof(Point));
    full_path->point_count = 0;
    full_path->total_cost = 0;

    // Reconstruction séquentielle
    for (uint32_t i = 0; i < tour_length - 1; i++)
    {
        uint32_t from = tour[i];
        uint32_t to = tour[i + 1];
        const Path *segment = path_matrix[from * poi_count + to];

        if (!segment)
            continue;

        // Copie des points (évite les doublons)
        uint32_t copy_count = segment->point_count;
        uint32_t start_offset = 0;

        if (i > 0 && full_path->point_count > 0)
        {
            start_offset = 1; // Évite la duplication du point de jonction
            copy_count--;
        }

        memcpy(full_path->points + full_path->point_count,
               segment->points + start_offset,
               copy_count * sizeof(Point));

        full_path->point_count += copy_count;
        full_path->total_cost += segment->total_cost;
    }

    return full_path;
}

void tsp_free_result(TSPResult *result)
{
    if (result)
    {
        free(result->tour);
        if (result->full_path)
        {
            free(result->full_path->points);
            free(result->full_path);
        }
        free(result);
    }
}
