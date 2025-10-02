#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "../include/geometry.h"

bool jps_validate_points(const Grid *grid, char **error_message)
{
    for (uint32_t i = 0; i < grid->poi_count; i++)
    {
        Point p = grid->points_of_interest[i];

        // Vérification des limites
        if (p.x < 0 || p.x >= (int)grid->width ||
            p.y < 0 || p.y >= (int)grid->height)
        {
            *error_message = malloc(256);
            snprintf(*error_message, 256,
                     "Point %d (%d, %d) hors limites de la grille (%d x %d)",
                     i, p.x, p.y, grid->width, grid->height);
            return false;
        }

        // Vérification collision avec obstacle
        if (grid->cells[p.y][p.x] == -1)
        {
            *error_message = malloc(256);
            snprintf(*error_message, 256,
                     "Point %d (%d, %d) en collision avec un obstacle",
                     i, p.x, p.y);
            return false;
        }

        // Vérification que c'est bien un point d'intérêt
        if (grid->cells[p.y][p.x] != 1)
        {
            *error_message = malloc(256);
            snprintf(*error_message, 256,
                     "Point %d (%d, %d) n'est pas marqué comme point d'intérêt (valeur: %d)",
                     i, p.x, p.y, grid->cells[p.y][p.x]);
            return false;
        }
    }

    return true;
}
