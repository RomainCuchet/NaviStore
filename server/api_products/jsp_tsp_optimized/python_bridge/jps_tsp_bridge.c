#include <Python.h>
#include "../common/include/common.h"
#include "../common/include/h5_loader.h"
#include "../common/include/geometry.h"
#include "../jps_module/include/jps.h"
#include "../tsp_module/include/tsp.h"

typedef struct
{
    PyObject_HEAD Grid *grid;
    JPSResult *jps_result;
    TSPResult *tsp_result;
} JTSolver;

static PyObject *jt_solver_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    JTSolver *self = (JTSolver *)type->tp_alloc(type, 0);
    if (self)
    {
        self->grid = NULL;
        self->jps_result = NULL;
        self->tsp_result = NULL;
    }
    return (PyObject *)self;
}

static int jt_solver_init(JTSolver *self, PyObject *args, PyObject *kwds)
{
    const char *h5_filename;
    static char *kwlist[] = {"h5_filename", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", kwlist, &h5_filename))
    {
        return -1;
    }

    // Chargement de la grille
    self->grid = jps_load_grid_from_h5(h5_filename);
    if (!self->grid)
    {
        PyErr_SetString(PyExc_RuntimeError, "Failed to load HDF5 file");
        return -1;
    }

    // Validation des points
    char *error_msg = NULL;
    if (!jps_validate_points(self->grid, &error_msg))
    {
        PyObject *py_err = Py_BuildValue("(ss)", "VALIDATION_ERROR", error_msg);
        PyErr_SetObject(PyExc_RuntimeError, py_err);
        free(error_msg);
        jps_free_grid(self->grid);
        return -1;
    }

    return 0;
}

static PyObject *jt_solver_compute_optimal_tour(JTSolver *self, PyObject *args)
{
    float threshold;
    const char *cache_path = NULL;

    if (!PyArg_ParseTuple(args, "f|s", &threshold, &cache_path))
    {
        return NULL;
    }

    // Étape 1: Calcul JPS
    self->jps_result = jps_compute_all_paths(self->grid, threshold, cache_path);
    if (!self->jps_result)
    {
        PyErr_SetString(PyExc_RuntimeError, "JPS computation failed");
        return NULL;
    }

    // Étape 2: Résolution TSP
    self->tsp_result = tsp_solve_optimal_tour(&self->jps_result->distance_matrix,
                                              (const Path **)self->jps_result->path_matrix,
                                              self->jps_result->poi_count);
    if (!self->tsp_result)
    {
        PyErr_SetString(PyExc_RuntimeError, "TSP solving failed");
        return NULL;
    }

    // Construction du résultat Python
    PyObject *result = PyDict_New();

    // Tour TSP
    PyObject *py_tour = PyList_New(self->tsp_result->tour_length);
    for (uint32_t i = 0; i < self->tsp_result->tour_length; i++)
    {
        PyList_SetItem(py_tour, i, PyLong_FromUnsignedLong(self->tsp_result->tour[i]));
    }
    PyDict_SetItemString(result, "tour", py_tour);

    // Distance totale
    PyDict_SetItemString(result, "total_distance",
                         PyFloat_FromDouble(self->tsp_result->total_distance));

    // Chemin complet
    if (self->tsp_result->full_path)
    {
        PyObject *py_path = PyList_New(self->tsp_result->full_path->point_count);
        for (uint32_t i = 0; i < self->tsp_result->full_path->point_count; i++)
        {
            Point p = self->tsp_result->full_path->points[i];
            PyObject *py_point = Py_BuildValue("(ii)", p.x, p.y);
            PyList_SetItem(py_path, i, py_point);
        }
        PyDict_SetItemString(result, "full_path", py_path);
    }

    // Métadonnées
    PyDict_SetItemString(result, "hedge_size", PyFloat_FromDouble(self->grid->hedge_size));
    PyDict_SetItemString(result, "poi_count", PyLong_FromUnsignedLong(self->grid->poi_count));

    return result;
}

static void jt_solver_dealloc(JTSolver *self)
{
    if (self->tsp_result)
        tsp_free_result(self->tsp_result);
    if (self->jps_result)
        jps_free_result(self->jps_result);
    if (self->grid)
        jps_free_grid(self->grid);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyMethodDef jt_solver_methods[] = {
    {"compute_optimal_tour", (PyCFunction)jt_solver_compute_optimal_tour,
     METH_VARARGS, "Compute optimal TSP tour using JPS paths"},
    {NULL, NULL, 0, NULL}};

static PyTypeObject JTSolverType = {
    PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "jps_tsp.JTSolver",
    .tp_doc = "JPS-TSP Solver",
    .tp_basicsize = sizeof(JTSolver),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = jt_solver_new,
    .tp_init = (initproc)jt_solver_init,
    .tp_dealloc = (destructor)jt_solver_dealloc,
    .tp_methods = jt_solver_methods,
};

static PyModuleDef jps_tsp_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "jps_tsp",
    .m_doc = "JPS with TSP integration using LKH",
    .m_size = -1,
};

PyMODINIT_FUNC PyInit_jps_tsp(void)
{
    PyObject *module = PyModule_Create(&jps_tsp_module);
    if (module == NULL)
        return NULL;

    if (PyType_Ready(&JTSolverType) < 0)
        return NULL;
    Py_INCREF(&JTSolverType);
    PyModule_AddObject(module, "JTSolver", (PyObject *)&JTSolverType);

    return module;
}
