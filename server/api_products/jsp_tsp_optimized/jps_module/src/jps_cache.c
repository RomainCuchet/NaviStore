#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../include/jps.h"

// Création d'un résultat JPS
JPSResult *jps_result_create(uint32_t poi_count)
{
    JPSResult *result = malloc(sizeof(JPSResult));
    result->poi_count = poi_count;
    result->distance_matrix.size = poi_count * poi_count;
    result->distance_matrix.data = malloc(result->distance_matrix.size * sizeof(float));
    result->path_matrix = malloc(result->distance_matrix.size * sizeof(Path *));

    for (uint32_t i = 0; i < result->distance_matrix.size; i++)
    {
        result->path_matrix[i] = NULL;
        result->distance_matrix.data[i] = INFINITY;
    }

    return result;
}

// Sauvegarde du cache
bool jps_cache_save(const JPSResult *result, const char *filename)
{
    char full_filename[512];
    snprintf(full_filename, sizeof(full_filename), "%s%s", filename, JPS_CACHE_EXTENSION);

    FILE *file = fopen(full_filename, "wb");
    if (!file)
        return false;

    // Écriture de l'en-tête
    char magic[4] = {'J', 'P', 'S', 1};
    fwrite(magic, sizeof(char), 4, file);
    uint32_t version = JPS_CACHE_VERSION;
    fwrite(&version, sizeof(uint32_t), 1, file);
    fwrite(&result->grid_hash, sizeof(uint64_t), 1, file);
    fwrite(&result->poi_count, sizeof(uint32_t), 1, file);

    // Écriture de la matrice des distances
    fwrite(result->distance_matrix.data, sizeof(float), result->distance_matrix.size, file);

    // Écriture des chemins
    for (uint32_t i = 0; i < result->distance_matrix.size; i++)
    {
        if (result->path_matrix[i])
        {
            uint16_t count = result->path_matrix[i]->point_count;
            fwrite(&count, sizeof(uint16_t), 1, file);
            fwrite(result->path_matrix[i]->points, sizeof(Point), count, file);
            fwrite(&result->path_matrix[i]->total_cost, sizeof(int16_t), 1, file);
        }
        else
        {
            uint16_t count = 0;
            fwrite(&count, sizeof(uint16_t), 1, file);
        }
    }

    fclose(file);
    return true;
}

// Chargement du cache
bool jps_cache_load(JPSResult *result, const char *filename, const Grid *grid)
{
    char full_filename[512];
    snprintf(full_filename, sizeof(full_filename), "%s%s", filename, JPS_CACHE_EXTENSION);

    FILE *file = fopen(full_filename, "rb");
    if (!file)
        return false;

    // Lecture de l'en-tête
    char magic[4];
    fread(magic, sizeof(char), 4, file);
    if (memcmp(magic, "JPS\\x01", 4) != 0)
    {
        fclose(file);
        return false;
    }

    uint32_t version;
    fread(&version, sizeof(uint32_t), 1, file);
    if (version != JPS_CACHE_VERSION)
    {
        fclose(file);
        return false;
    }

    uint64_t grid_hash;
    fread(&grid_hash, sizeof(uint64_t), 1, file);
    if (grid_hash != compute_grid_hash(grid))
    {
        fclose(file);
        return false;
    }

    uint32_t poi_count;
    fread(&poi_count, sizeof(uint32_t), 1, file);
    if (poi_count != result->poi_count)
    {
        fclose(file);
        return false;
    }

    result->grid_hash = grid_hash;

    // Lecture de la matrice des distances
    fread(result->distance_matrix.data, sizeof(float), result->distance_matrix.size, file);

    // Lecture des chemins
    for (uint32_t i = 0; i < result->distance_matrix.size; i++)
    {
        uint16_t count;
        fread(&count, sizeof(uint16_t), 1, file);
        if (count > 0)
        {
            result->path_matrix[i] = malloc(sizeof(Path));
            result->path_matrix[i]->point_count = count;
            result->path_matrix[i]->points = malloc(count * sizeof(Point));
            fread(result->path_matrix[i]->points, sizeof(Point), count, file);
            fread(&result->path_matrix[i]->total_cost, sizeof(int16_t), 1, file);
        }
    }

    fclose(file);
    return true;
}

void jps_free_result(JPSResult *result)
{
    if (result)
    {
        free(result->distance_matrix.data);
        for (uint32_t i = 0; i < result->distance_matrix.size; i++)
        {
            if (result->path_matrix[i])
            {
                free(result->path_matrix[i]->points);
                free(result->path_matrix[i]);
            }
        }
        free(result->path_matrix);
        free(result);
    }
}
