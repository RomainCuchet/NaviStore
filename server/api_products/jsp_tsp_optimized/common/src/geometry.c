#include "../include/common.h"

uint64_t compute_grid_hash(const Grid *grid)
{
    // Une fonction de hachage simple pour la grille
    uint64_t hash = 0;
    for (uint32_t y = 0; y < grid->height; y++)
    {
        for (uint32_t x = 0; x < grid->width; x++)
        {
            hash = hash * 31 + grid->cells[y][x];
        }
    }
    hash = hash * 31 + grid->poi_count;
    return hash;
}

bool validate_point(const Grid *grid, Point p)
{
    return p.x >= 0 && p.x < (int)grid->width &&
           p.y >= 0 && p.y < (int)grid->height &&
           grid->cells[p.y][p.x] != -1;
}

float euclidean_distance(Point a, Point b)
{
    int dx = a.x - b.x;
    int dy = a.y - b.y;
    return sqrtf(dx * dx + dy * dy);
}

int16_t manhattan_distance(Point a, Point b)
{
    return abs(a.x - b.x) + abs(a.y - b.y);
}
