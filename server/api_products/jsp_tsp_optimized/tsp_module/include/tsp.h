#ifndef TSP_H
#define TSP_H

#include "../common/include/common.h"

typedef struct
{
    uint32_t *tour; // [0, 2, 1, 0] - ordre de visite
    uint32_t tour_length;
    float total_distance;
    Path *full_path; // Chemin complet reconstruit
} TSPResult;

// API TSP
TSPResult *tsp_solve_optimal_tour(const DistanceMatrix *matrix,
                                  const Path **path_matrix,
                                  uint32_t poi_count);
void tsp_free_result(TSPResult *result);

// Intégration LKH
bool lkh_solve_tsp(const DistanceMatrix *matrix, uint32_t *tour, float *total_distance);
Path *tsp_reconstruct_full_path(const uint32_t *tour, uint32_t tour_length,
                                const Path **path_matrix, uint32_t poi_count);

#endif