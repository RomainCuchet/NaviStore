#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/tsp.h"
#ifdef _WIN32
#include <io.h>
#define close _close
#define mkstemps _mktemp_s
#else
#include <unistd.h>
#endif

// Génération du fichier TSP pour LKH
static bool generate_tsp_file(const DistanceMatrix *matrix, const char *filename)
{
    FILE *file = fopen(filename, "w");
    if (!file)
        return false;

    uint32_t dimension = matrix->size;

    fprintf(file, "NAME: JPS_TSP_PROBLEM\\n");
    fprintf(file, "TYPE: TSP\\n");
    fprintf(file, "DIMENSION: %u\\n", dimension);
    fprintf(file, "EDGE_WEIGHT_TYPE: EXPLICIT\\n");
    fprintf(file, "EDGE_WEIGHT_FORMAT: FULL_MATRIX\\n");
    fprintf(file, "EDGE_WEIGHT_SECTION\\n");

    // Écriture de la matrice
    for (uint32_t i = 0; i < dimension; i++)
    {
        for (uint32_t j = 0; j < dimension; j++)
        {
            // LKH attend des entiers, conversion avec précision
            int cost = (int)(matrix->data[i * dimension + j] * 1000.0f);
            if (cost == 0 && i != j)
                cost = 999999; // Évite les zéros pour les connexions manquantes
            fprintf(file, "%d ", cost);
        }
        fprintf(file, "\\n");
    }

    fprintf(file, "EOF\\n");
    fclose(file);
    return true;
}

// Lecture du résultat LKH
static bool read_lkh_solution(const char *filename, uint32_t *tour, uint32_t size, float *total_distance)
{
    FILE *file = fopen(filename, "r");
    if (!file)
        return false;

    char line[256];
    bool in_tour_section = false;
    uint32_t index = 0;

    while (fgets(line, sizeof(line), file))
    {
        if (strstr(line, "TOUR_SECTION"))
        {
            in_tour_section = true;
            continue;
        }

        if (in_tour_section)
        {
            int city = atoi(line);
            if (city == -1)
                break;

            if (city > 0)
            {
                // LKH utilise base 1, conversion base 0
                if (index < size)
                {
                    tour[index++] = city - 1;
                }
                if (index >= size)
                    break;
            }
        }

        // Extraction de la distance totale
        if (strstr(line, "COMMENT"))
        {
            char *dist_str = strstr(line, "Length =");
            if (dist_str)
            {
                *total_distance = atof(dist_str + 8) / 1000.0f;
            }
        }
    }

    fclose(file);
    return (index == size);
}

// Résolution TSP avec LKH
bool lkh_solve_tsp(const DistanceMatrix *matrix, uint32_t *tour, float *total_distance)
{
    char tsp_file[] = "/tmp/jps_tsp_XXXXXX.tsp";
    char sol_file[] = "/tmp/jps_tsp_XXXXXX.sol";
    char par_file[] = "/tmp/jps_tsp_XXXXXX.par";

    // Création fichiers temporaires
    int fd_tsp = mkstemps(tsp_file, 4);
    int fd_sol = mkstemps(sol_file, 4);
    int fd_par = mkstemps(par_file, 4);

    if (fd_tsp == -1 || fd_sol == -1 || fd_par == -1)
    {
        return false;
    }

    close(fd_tsp);
    close(fd_sol);
    close(fd_par);

    // Génération fichier TSP
    if (!generate_tsp_file(matrix, tsp_file))
    {
        remove(tsp_file);
        remove(sol_file);
        remove(par_file);
        return false;
    }

    // Génération fichier de paramètres LKH
    FILE *par = fopen(par_file, "w");
    if (!par)
    {
        remove(tsp_file);
        remove(sol_file);
        remove(par_file);
        return false;
    }

    fprintf(par, "PROBLEM_FILE = %s\\n", tsp_file);
    fprintf(par, "TOUR_FILE = %s\\n", sol_file);
    fprintf(par, "RUNS = 1\\n");
    fprintf(par, "TIME_LIMIT = 30\\n"); // 30 secondes max
    fprintf(par, "TRACE_LEVEL = 0\\n");
    fclose(par);

    // Exécution LKH
    char command[512];
    snprintf(command, sizeof(command), "LKH %s 2>/dev/null", par_file);
    int ret = system(command);

    bool success = false;
    if (ret == 0)
    {
        success = read_lkh_solution(sol_file, tour, matrix->size + 1, total_distance);
    }

    // Nettoyage
    remove(tsp_file);
    remove(sol_file);
    remove(par_file);

    return success;
}
