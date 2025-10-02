#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#pragma pack(push, 1)
typedef struct
{
    int16_t x, y;
} Point;

typedef struct
{
    Point *points;
    uint16_t point_count;
    int16_t total_cost;
} Path;

typedef struct
{
    int8_t **cells;
    uint32_t width;
    uint32_t height;
    Point *points_of_interest;
    uint32_t poi_count;
    float hedge_size;
    char *h5_filename;
} Grid;

typedef struct
{
    float *data;
    uint32_t size;
} DistanceMatrix;
#pragma pack(pop)

uint64_t compute_grid_hash(const Grid *grid);
bool validate_point(const Grid *grid, Point p);
float euclidean_distance(Point a, Point b);
int16_t manhattan_distance(Point a, Point b);

#endif
