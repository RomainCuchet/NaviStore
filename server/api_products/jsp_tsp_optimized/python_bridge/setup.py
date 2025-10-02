from distutils.core import setup, Extension
import os
import subprocess
import sys

# Configuration
USE_HDF5 = True  # Mettre à False si HDF5 n'est pas disponible
USE_LKH = True  # Mettre à False si LKH n'est pas disponible


def check_hdf5():
    try:
        subprocess.run(
            ["pkg-config", "--exists", "hdf5"], check=True, capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("HDF5 not found. Install with: sudo apt-get install libhdf5-dev")
        return False


def check_lkh():
    # Vérifie si LKH est disponible dans le PATH
    try:
        subprocess.run(["which", "LKH"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        print("LKH not found in PATH. Please install LKH and ensure it's in your PATH")
        return False


# Vérification des dépendances
hdf5_available = check_hdf5() if USE_HDF5 else False
lkh_available = check_lkh() if USE_LKH else False

# Configuration de compilation
compile_args = ["-O3", "-march=native", "-ffast-math", "-DNDEBUG"]
define_macros = [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]

if hdf5_available:
    define_macros.append(("USE_HDF5", "1"))
    libraries = ["hdf5", "hdf5_hl"]
else:
    libraries = []

if not lkh_available:
    print("Warning: LKH not available, using fallback TSP solver")

# Sources
sources = [
    "jps_tsp_bridge.c",
    "../common/src/h5_loader.c",
    "../common/src/collision_checker.c",
    "../common/src/geometry.c",
    "../jps_module/src/jps_core.c",
    "../jps_module/src/jps_cache.c",
    "../jps_module/src/jps_matrix.c",
    "../jps_module/src/jps_path.c",
    "../tsp_module/src/tsp_solver.c",
    "../tsp_module/src/lkh_interface.c",
]

jps_tsp_module = Extension(
    "jps_tsp",
    sources=sources,
    include_dirs=[
        "../common/include",
        "../jps_module/include",
        "../tsp_module/include",
    ],
    libraries=libraries,
    extra_compile_args=compile_args,
    define_macros=define_macros,
)

setup(
    name="jps_tsp",
    version="1.0",
    description="Optimal path planning with JPS and TSP integration",
    ext_modules=[jps_tsp_module],
)
