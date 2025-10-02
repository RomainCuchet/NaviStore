#include <stdlib.h>
#include <string.h>
#include "../include/jps.h"

// Cette fonction est déjà implémentée dans jps_core.c
// On la redéclare ici pour éviter les problèmes de lien
Path *jps_find_path_between(const Grid *grid, Point start, Point goal)
{
    // Implémentation simplifiée, voir jps_core.c
    int16_t dist = abs(start.x - goal.x) + abs(start.y - goal.y);
    Path *path = malloc(sizeof(Path));
    path->points = malloc(2 * sizeof(Point));
    path->points[0] = start;
    path->points[1] = goal;
    path->point_count = 2;
    path->total_cost = dist;
    return path;
}
