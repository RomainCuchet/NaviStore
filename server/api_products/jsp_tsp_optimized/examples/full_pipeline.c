#include "../common/include/common.h"
#include "../jps_module/include/jps.h"
#include "../tsp_module/include/tsp.h"
#include <stdio.h>

int main()
{
    printf("🚀 JPS-TSP Pipeline Démarrage...\\n");

    // Étape 1: Chargement
    Grid *grid = jps_load_grid_from_h5("data/urban_grid.h5");
    if (!grid)
    {
        // Création d'une grille de test
        printf("Création d'une grille de test...\\n");
        grid = malloc(sizeof(Grid));
        grid->width = 10;
        grid->height = 10;
        grid->hedge_size = 1.0f;
        grid->poi_count = 4;

        // Allocation de la grille
        grid->cells = malloc(grid->height * sizeof(int8_t *));
        for (uint32_t i = 0; i < grid->height; i++)
        {
            grid->cells[i] = malloc(grid->width * sizeof(int8_t));
            for (uint32_t j = 0; j < grid->width; j++)
            {
                grid->cells[i][j] = 0; // Toutes les cases libres
            }
        }

        // Points d'intérêt
        grid->points_of_interest = malloc(grid->poi_count * sizeof(Point));
        grid->points_of_interest[0] = (Point){1, 1};
        grid->points_of_interest[1] = (Point){8, 1};
        grid->points_of_interest[2] = (Point){1, 8};
        grid->points_of_interest[3] = (Point){8, 8};

        // Marquer les points dans la grille
        for (uint32_t i = 0; i < grid->poi_count; i++)
        {
            Point p = grid->points_of_interest[i];
            grid->cells[p.y][p.x] = 1;
        }
    }

    // Étape 2: Validation
    char *error_msg;
    if (!jps_validate_points(grid, &error_msg))
    {
        printf("❌ Validation échouée: %s\\n", error_msg);
        free(error_msg);
        jps_free_grid(grid);
        return 1;
    }

    printf("✅ Grille chargée: %dx%d, %d POI\\n",
           grid->width, grid->height, grid->poi_count);

    // Étape 3: Calcul JPS
    JPSResult *jps_result = jps_compute_all_paths(grid, 100.0f, "jps_cache");
    if (!jps_result)
    {
        printf("❌ Erreur calcul JPS\\n");
        jps_free_grid(grid);
        return 1;
    }

    printf("✅ Matrice JPS calculée: %d×%d\\n", jps_result->poi_count, jps_result->poi_count);

    // Étape 4: Résolution TSP
    TSPResult *tsp_result = tsp_solve_optimal_tour(&jps_result->distance_matrix,
                                                   (const Path **)jps_result->path_matrix,
                                                   jps_result->poi_count);
    if (!tsp_result)
    {
        printf("❌ Erreur résolution TSP\\n");
        jps_free_result(jps_result);
        jps_free_grid(grid);
        return 1;
    }

    printf("✅ Tour TSP optimal trouvé!\\n");
    printf("   Distance totale: %.2f\\n", tsp_result->total_distance);
    printf("   Ordre de visite: ");
    for (uint32_t i = 0; i < tsp_result->tour_length; i++)
    {
        printf("%d ", tsp_result->tour[i]);
    }
    printf("\\n");
    printf("   Chemin complet: %d points\\n", tsp_result->full_path->point_count);

    // Nettoyage
    tsp_free_result(tsp_result);
    jps_free_result(jps_result);
    jps_free_grid(grid);

    printf("✅ Pipeline terminé avec succès!\\n");
    return 0;
}
