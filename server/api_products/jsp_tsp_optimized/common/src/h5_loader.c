#ifdef USE_HDF5
#include <hdf5.h>
#endif
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "../include/h5_loader.h"

Grid *jps_load_grid_from_h5(const char *filename)
{
#ifdef USE_HDF5
    hid_t file_id = H5Fopen(filename, H5F_ACC_RDONLY, H5P_DEFAULT);
    if (file_id < 0)
    {
        fprintf(stderr, "Cannot open HDF5 file: %s\\n", filename);
        return NULL;
    }

    Grid *grid = malloc(sizeof(Grid));
    grid->h5_filename = strdup(filename);

    // Chargement de la matrice
    hid_t dataset_id = H5Dopen2(file_id, "/matrix", H5P_DEFAULT);
    if (dataset_id < 0)
    {
        fprintf(stderr, "Cannot open /matrix dataset\\n");
        H5Fclose(file_id);
        free(grid->h5_filename);
        free(grid);
        return NULL;
    }

    hid_t dataspace_id = H5Dget_space(dataset_id);
    int ndims = H5Sget_simple_extent_ndims(dataspace_id);
    hsize_t dims[ndims];
    H5Sget_simple_extent_dims(dataspace_id, dims, NULL);

    grid->height = dims[0];
    grid->width = dims[1];

    // Allocation et lecture
    grid->cells = malloc(grid->height * sizeof(int8_t *));
    for (uint32_t i = 0; i < grid->height; i++)
    {
        grid->cells[i] = malloc(grid->width * sizeof(int8_t));
    }

    H5Dread(dataset_id, H5T_NATIVE_INT8, H5S_ALL, H5S_ALL, H5P_DEFAULT, grid->cells);

    // Chargement hedge_size
    hid_t attr_id = H5Aopen_by_name(file_id, "/matrix", "hedge_size", H5P_DEFAULT, H5P_DEFAULT);
    if (attr_id >= 0)
    {
        H5Aread(attr_id, H5T_NATIVE_FLOAT, &grid->hedge_size);
        H5Aclose(attr_id);
    }
    else
    {
        grid->hedge_size = 1.0f; // Valeur par défaut
    }

    // Chargement points d'intérêt
    hid_t points_dataset = H5Dopen2(file_id, "/points_of_interest", H5P_DEFAULT);
    if (points_dataset >= 0)
    {
        hid_t points_space = H5Dget_space(points_dataset);
        hsize_t points_dims[2];
        H5Sget_simple_extent_dims(points_space, points_dims, NULL);
        grid->poi_count = points_dims[0];

        grid->points_of_interest = malloc(grid->poi_count * sizeof(Point));
        int16_t *points_data = malloc(grid->poi_count * 2 * sizeof(int16_t));
        H5Dread(points_dataset, H5T_NATIVE_INT16, H5S_ALL, H5S_ALL, H5P_DEFAULT, points_data);

        for (uint32_t i = 0; i < grid->poi_count; i++)
        {
            grid->points_of_interest[i].x = points_data[i * 2];
            grid->points_of_interest[i].y = points_data[i * 2 + 1];
        }

        free(points_data);
        H5Dclose(points_dataset);
    }
    else
    {
        // Fallback: détection automatique des points d'intérêt
        grid->poi_count = 0;
        for (uint32_t y = 0; y < grid->height; y++)
        {
            for (uint32_t x = 0; x < grid->width; x++)
            {
                if (grid->cells[y][x] == 1)
                    grid->poi_count++;
            }
        }

        grid->points_of_interest = malloc(grid->poi_count * sizeof(Point));
        uint32_t idx = 0;
        for (uint32_t y = 0; y < grid->height; y++)
        {
            for (uint32_t x = 0; x < grid->width; x++)
            {
                if (grid->cells[y][x] == 1)
                {
                    grid->points_of_interest[idx].x = x;
                    grid->points_of_interest[idx].y = y;
                    idx++;
                }
            }
        }
    }

    // Nettoyage
    H5Dclose(dataset_id);
    H5Fclose(file_id);

    return grid;
#else
    fprintf(stderr, "HDF5 support not compiled\\n");
    return NULL;
#endif
}

void jps_free_grid(Grid *grid)
{
    if (grid)
    {
        for (uint32_t i = 0; i < grid->height; i++)
        {
            free(grid->cells[i]);
        }
        free(grid->cells);
        free(grid->points_of_interest);
        free(grid->h5_filename);
        free(grid);
    }
}