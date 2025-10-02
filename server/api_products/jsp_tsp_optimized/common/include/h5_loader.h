#ifndef H5_LOADER_H
#define H5_LOADER_H

#include "common.h"

Grid *jps_load_grid_from_h5(const char *filename);
void jps_free_grid(Grid *grid);

#endif