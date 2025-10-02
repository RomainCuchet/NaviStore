# Compilateur et flags
CC = gcc
CFLAGS = -O3 -march=native -ffast-math -DNDEBUG -std=c99 -Wall -Wextra
LDFLAGS = -lm

# Dossiers
SRC_DIR = .
COMMON_DIR = common
JPS_DIR = jps_module
TSP_DIR = tsp_module
BUILD_DIR = build
EXAMPLES_DIR = examples

# Sources
COMMON_SRCS = $(wildcard $(COMMON_DIR)/src/*.c)
JPS_SRCS = $(wildcard $(JPS_DIR)/src/*.c)
TSP_SRCS = $(wildcard $(TSP_DIR)/src/*.c)
EXAMPLES_SRCS = $(wildcard $(EXAMPLES_DIR)/*.c)

# Headers
INCLUDES = -I$(COMMON_DIR)/include -I$(JPS_DIR)/include -I$(TSP_DIR)/include

# Cibles
TARGET = $(BUILD_DIR)/jps_tsp_demo

# Règles par défaut
all: $(TARGET)

# Création du dossier build
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compilation principale
$(TARGET): $(BUILD_DIR) $(COMMON_SRCS) $(JPS_SRCS) $(TSP_SRCS) $(EXAMPLES_SRCS)
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $(COMMON_SRCS) $(JPS_SRCS) $(TSP_SRCS) $(EXAMPLES_SRCS) $(LDFLAGS)

# Nettoyage
clean:
	rm -rf $(BUILD_DIR)
	rm -f *.jps

# Installation Python
python:
	cd python_bridge && python setup.py build_ext --inplace

# Test
test: $(TARGET)
	./$(TARGET)

.PHONY: all clean python test