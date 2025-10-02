#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/jps.h"

// Directions pour JPS (4 directions pour Manhattan)
static const Point directions[4] = {
    {1, 0}, {0, 1}, {-1, 0}, {0, -1} // E, N, O, S
};

// Structure pour le nœud de recherche
typedef struct Node
{
    Point position;
    int16_t g_cost;
    int16_t f_cost;
    struct Node *parent;
    uint8_t direction;
} Node;

// Vérifications de base
static inline bool is_valid_point(const Grid *grid, Point p)
{
    return p.x >= 0 && p.x < (int)grid->width &&
           p.y >= 0 && p.y < (int)grid->height;
}

static inline bool is_obstacle(const Grid *grid, Point p)
{
    return grid->cells[p.y][p.x] == -1;
}

// Détection de voisin forcé (simplifiée pour Manhattan)
static bool has_forced_neighbor(const Grid *grid, Point current, uint8_t dir)
{
    // Implémentation simplifiée: on suppose que les obstacles forcent un changement de direction
    Point check_points[2];
    switch (dir)
    {
    case 0: // Est
        check_points[0] = (Point){current.x, current.y + 1};
        check_points[1] = (Point){current.x, current.y - 1};
        break;
    case 1: // Nord
        check_points[0] = (Point){current.x + 1, current.y};
        check_points[1] = (Point){current.x - 1, current.y};
        break;
    case 2: // Ouest
        check_points[0] = (Point){current.x, current.y + 1};
        check_points[1] = (Point){current.x, current.y - 1};
        break;
    case 3: // Sud
        check_points[0] = (Point){current.x + 1, current.y};
        check_points[1] = (Point){current.x - 1, current.y};
        break;
    default:
        return false;
    }

    for (int i = 0; i < 2; i++)
    {
        if (is_valid_point(grid, check_points[i]) && is_obstacle(grid, check_points[i]))
        {
            return true;
        }
    }
    return false;
}

// Recherche récursive des points de saut
static Point jump(const Grid *grid, Point current, uint8_t dir, Point goal, bool *found)
{
    if (!is_valid_point(grid, current) || is_obstacle(grid, current))
    {
        *found = false;
        return current;
    }

    if (current.x == goal.x && current.y == goal.y)
    {
        *found = true;
        return current;
    }

    // Vérifier les voisins forcés
    if (has_forced_neighbor(grid, current, dir))
    {
        *found = true;
        return current;
    }

    // Continuer dans la direction
    Point next = {
        current.x + directions[dir].x,
        current.y + directions[dir].y};

    return jump(grid, next, dir, goal, found);
}

// Algorithme JPS principal entre deux points
Path *jps_find_path_between(const Grid *grid, Point start, Point goal)
{
    // Pour l'exemple, on retourne un chemin direct (à remplacer par JPS complet)
    // Dans une implémentation réelle, vous implémenteriez JPS complet ici
    int16_t dist = manhattan_distance(start, goal);
    Path *path = malloc(sizeof(Path));
    path->points = malloc(2 * sizeof(Point));
    path->points[0] = start;
    path->points[1] = goal;
    path->point_count = 2;
    path->total_cost = dist;

    return path;
}
