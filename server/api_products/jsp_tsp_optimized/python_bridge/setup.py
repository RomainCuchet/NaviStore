from distutils.core import setup, Extension
import os
import subprocess
import sys

# Configuration
USE_HDF5 = True  # Mettre à False si HDF5 n'est pas disponible
USE_LKH = True  # Mettre à False si LKH n'est pas disponible


def get_python_config():
    """Récupère les flags de compilation Python"""
    try:
        includes = subprocess.check_output(["python3-config", "--includes"]).decode().strip().split()
        ldflags = subprocess.check_output(["python3-config", "--ldflags"]).decode().strip().split()
        return includes, ldflags
    except subprocess.CalledProcessError:
        print("Warning: python3-config not found, using default paths")
        return [], []


def check_hdf5():
    try:
        subprocess.run(
            ["pkg-config", "--exists", "hdf5"], check=True, capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("HDF5 not found. Install with: sudo apt-get install libhdf5-dev")
        return False


def get_hdf5_config():
    """Récupère les flags de compilation et de liaison pour HDF5"""
    try:
        cflags = subprocess.check_output(["pkg-config", "--cflags", "hdf5"]).decode().strip().split()
        libs = subprocess.check_output(["pkg-config", "--libs", "hdf5"]).decode().strip().split()
        return cflags, libs
    except subprocess.CalledProcessError:
        print("Warning: pkg-config failed for HDF5")
        return [], []


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

# Récupération de la configuration Python
python_includes, python_ldflags = get_python_config()

# Récupération de la configuration HDF5
hdf5_cflags, hdf5_libs = get_hdf5_config() if hdf5_available else ([], [])

# Configuration de compilation
compile_args = ["-O3", "-march=native", "-ffast-math", "-DNDEBUG"]
# Ajout des flags Python
for flag in python_includes:
    if flag.startswith('-I'):
        compile_args.append(flag)
# Ajout des flags HDF5
compile_args.extend(hdf5_cflags)

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
    "../tsp_module/src/tsp_sovler.c",
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
    extra_link_args=[flag for flag in python_ldflags + hdf5_libs if not flag.startswith('-I')],
    define_macros=define_macros,
)

setup(
    name="jps_tsp",
    version="1.0",
    description="Optimal path planning with JPS and TSP integration",
    ext_modules=[jps_tsp_module],
)
