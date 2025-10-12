import numpy as np
import h5py
import os
import sys
from typing import List, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from api_navimall.path_optimization.utils import (
    load_layout_from_h5,
    save_grid_with_metadata,
    calculate_layout_hash,
    Zone,
)

# Create new layout with specified dimensions
WIDTH = 250
HEIGHT = 250
EDGE_LENGTH = 40  # cm per grid cell

layout = np.zeros((HEIGHT, WIDTH), dtype=np.int8)
edge_length = EDGE_LENGTH
zones_dict = {}  # Empty zones dictionary for new layout

print(f"🏬 Génération d'un layout de supermarché réaliste")
print(f"📏 Dimensions: {layout.shape}, edge_length: {edge_length} cm")

# Reset the entire layout to navigable space (0)
layout.fill(0)

# Set borders as obstacles (-1)
layout[0, :] = -1  # Top border
layout[-1, :] = -1  # Bottom border
layout[:, 0] = -1  # Left border
layout[:, -1] = -1  # Right border

# Supermarket layout parameters (in cm, converted to grid cells)
CENTRAL_AISLE_WIDTH_CM = 400  # 4m wide central aisle aligned with entrance (increased)
SIDE_AISLE_WIDTH_CM = 200  # 2m wide side aisles (increased)
INTER_SHELF_AISLE_CM = 200  # 2m wide aisles between shelf sections (new)
SHELF_WIDTH_CM = 120  # 1.2m wide shelves
SHELF_LENGTH_CM = 600  # 6m long shelves (more manageable)
ENTRANCE_WIDTH_CM = 400  # 4m wide entrance

# Convert to grid cells (ensure minimum of 4 cells)
central_aisle_width = max(4, round(CENTRAL_AISLE_WIDTH_CM / edge_length))
side_aisle_width = max(4, round(SIDE_AISLE_WIDTH_CM / edge_length))
inter_shelf_aisle_width = max(4, round(INTER_SHELF_AISLE_CM / edge_length))
shelf_width = max(1, round(SHELF_WIDTH_CM / edge_length))
shelf_length = max(1, round(SHELF_LENGTH_CM / edge_length))
entrance_width = max(4, round(ENTRANCE_WIDTH_CM / edge_length))

# Load the reference layout to get dimensions and edge_length
LAYOUT_PATH = "../../api_navimall/assets/6f0f94d5ad19adb2.h5"
layout, edge_length, zones_dict = load_layout_from_h5(LAYOUT_PATH)

print(f"🏬 Génération d'un layout de supermarché réaliste")
print(f"📏 Dimensions: {layout.shape}, edge_length: {edge_length} cm")

# Reset the entire layout to navigable space (0)
layout.fill(0)

# Set borders as obstacles (-1)
layout[0, :] = -1  # Top border
layout[-1, :] = -1  # Bottom border
layout[:, 0] = -1  # Left border
layout[:, -1] = -1  # Right border

# Supermarket layout parameters (in cm, converted to grid cells)
CENTRAL_AISLE_WIDTH_CM = 300  # 3m wide central aisle aligned with entrance
SIDE_AISLE_WIDTH_CM = 150  # 1.5m wide side aisles
SHELF_WIDTH_CM = 120  # 1.2m wide shelves
SHELF_LENGTH_CM = 600  # 6m long shelves (more manageable)
ENTRANCE_WIDTH_CM = 400  # 4m wide entrance

# Convert to grid cells
central_aisle_width = max(1, round(CENTRAL_AISLE_WIDTH_CM / edge_length))
side_aisle_width = max(1, round(SIDE_AISLE_WIDTH_CM / edge_length))
shelf_width = max(1, round(SHELF_WIDTH_CM / edge_length))
shelf_length = max(1, round(SHELF_LENGTH_CM / edge_length))
entrance_width = max(1, round(ENTRANCE_WIDTH_CM / edge_length))

# Calculate center positions
center_x = layout.shape[1] // 2
center_y = layout.shape[0] // 2

# Create entrance at the bottom center
entrance_start = center_x - entrance_width // 2
entrance_end = center_x + entrance_width // 2
layout[-1, entrance_start:entrance_end] = 0  # Remove border for entrance

print(f"🏗️  Construction du layout avec allée centrale...")

# Create central aisle aligned with entrance (north-south)
central_aisle_start = center_x - central_aisle_width // 2
central_aisle_end = center_x + central_aisle_width // 2
# Keep central aisle clear from entrance to top (but leave space at top for cross aisle)
layout[side_aisle_width:-side_aisle_width, central_aisle_start:central_aisle_end] = 0

# Create main cross aisle (east-west) at 1/3 from top
cross_aisle_y = layout.shape[0] // 3
layout[
    cross_aisle_y : cross_aisle_y + side_aisle_width, side_aisle_width:-side_aisle_width
] = 0

# Create perimeter aisles (next to walls)
# Top perimeter aisle
layout[1 : 1 + side_aisle_width, 1:-1] = 0
# Bottom perimeter aisle (but keep entrance area)
layout[-side_aisle_width - 1 : -1, 1:entrance_start] = 0  # Left of entrance
layout[-side_aisle_width - 1 : -1, entrance_end:-1] = 0  # Right of entrance
# Left perimeter aisle
layout[1:-1, 1 : 1 + side_aisle_width] = 0
# Right perimeter aisle
layout[1:-1, -side_aisle_width - 1 : -1] = 0

print(f"🛒 Placement des blocs d'étagères organisés...")

# Define shelf block areas (avoiding aisles)
# Left side blocks
left_blocks = [
    # Top left block
    {
        "start_x": 1 + side_aisle_width,
        "end_x": central_aisle_start,
        "start_y": 1 + side_aisle_width,
        "end_y": cross_aisle_y,
    },
    # Bottom left block
    {
        "start_x": 1 + side_aisle_width,
        "end_x": central_aisle_start,
        "start_y": cross_aisle_y + side_aisle_width,
        "end_y": layout.shape[0] - side_aisle_width - 1,
    },
]

# Right side blocks (mirror of left)
right_blocks = [
    # Top right block
    {
        "start_x": central_aisle_end,
        "end_x": layout.shape[1] - side_aisle_width - 1,
        "start_y": 1 + side_aisle_width,
        "end_y": cross_aisle_y,
    },
    # Bottom right block
    {
        "start_x": central_aisle_end,
        "end_x": layout.shape[1] - side_aisle_width - 1,
        "start_y": cross_aisle_y + side_aisle_width,
        "end_y": layout.shape[0] - side_aisle_width - 1,
    },
]

all_blocks = left_blocks + right_blocks

# Fill each block with organized shelves
for block_idx, block in enumerate(all_blocks):
    print(
        f"   📦 Bloc {block_idx + 1}: ({block['start_x']},{block['start_y']}) -> ({block['end_x']},{block['end_y']})"
    )

    block_width = block["end_x"] - block["start_x"]
    block_height = block["end_y"] - block["start_y"]

    # Skip if block is too small
    if block_width < shelf_width * 2 or block_height < shelf_length:
        continue

    # Calculate how many shelf rows we can fit with minimum 4-cell aisles
    mini_aisle = max(
        4, inter_shelf_aisle_width
    )  # Ensure minimum 4 cells between shelves
    available_width = block_width
    shelf_rows = max(1, available_width // (shelf_width + mini_aisle))

    # Calculate actual spacing
    total_shelf_width = shelf_rows * shelf_width
    total_aisle_width = (shelf_rows - 1) * mini_aisle
    remaining_space = block_width - total_shelf_width - total_aisle_width
    margin = max(0, remaining_space // 2)

    print(
        f"     - Rangées d'étagères: {shelf_rows}, espacement: {mini_aisle} cells (≥4)"
    )

    # Place shelf rows in this block with cross-aisles
    current_x = block["start_x"] + margin
    for row in range(shelf_rows):
        if current_x + shelf_width <= block["end_x"]:
            # Add cross-aisle in middle of block for better navigation
            mid_block_y = block["start_y"] + block_height // 2
            cross_aisle_width = max(4, mini_aisle // 2)

            # Place shelves in top half
            current_y = block["start_y"]
            while current_y + shelf_length <= mid_block_y - cross_aisle_width:
                layout[
                    current_y : current_y + shelf_length,
                    current_x : current_x + shelf_width,
                ] = 2
                current_y += shelf_length + max(
                    4, mini_aisle // 2
                )  # Minimum 4 cells between shelf sections

                if current_y < mid_block_y - cross_aisle_width:
                    remaining_length = mid_block_y - cross_aisle_width - current_y
                    if remaining_length >= 4:  # Minimum shelf size
                        layout[
                            current_y : mid_block_y - cross_aisle_width,
                            current_x : current_x + shelf_width,
                        ] = 2
                    break

            # Place shelves in bottom half
            current_y = mid_block_y + cross_aisle_width
            while current_y + shelf_length <= block["end_y"]:
                layout[
                    current_y : current_y + shelf_length,
                    current_x : current_x + shelf_width,
                ] = 2
                current_y += shelf_length + max(
                    4, mini_aisle // 2
                )  # Minimum 4 cells between shelf sections

                if current_y < block["end_y"]:
                    remaining_length = block["end_y"] - current_y
                    if remaining_length >= 4:  # Minimum shelf size
                        layout[
                            current_y : block["end_y"],
                            current_x : current_x + shelf_width,
                        ] = 2
                    break

            current_x += shelf_width + mini_aisle

# Add cross-aisles within blocks for improved navigation
print(f"🛤️  Ajout d'allées transversales supplémentaires dans les blocs...")
for block_idx, block in enumerate(all_blocks):
    block_width = block["end_x"] - block["start_x"]
    block_height = block["end_y"] - block["start_y"]

    # Add horizontal cross-aisle in middle of each block
    mid_y = block["start_y"] + block_height // 2
    cross_aisle_width = max(4, inter_shelf_aisle_width // 2)
    layout[mid_y : mid_y + cross_aisle_width, block["start_x"] : block["end_x"]] = 0

    # Add vertical aisle in wider blocks
    if block_width > shelf_width * 3:
        mid_x = block["start_x"] + block_width // 2
        vertical_aisle_width = max(4, inter_shelf_aisle_width // 2)
        layout[
            block["start_y"] : block["end_y"], mid_x : mid_x + vertical_aisle_width
        ] = 0

# Add perimeter shelves touching walls
perimeter_shelf_depth = max(1, round(80 / edge_length))  # 80cm deep

# Top wall shelves (touching wall)
layout[1 : 1 + perimeter_shelf_depth, 1:-1] = 2

# Left wall shelves (touching wall)
layout[1:-1, 1 : 1 + perimeter_shelf_depth] = 2

# Right wall shelves (touching wall)
layout[1:-1, -perimeter_shelf_depth - 1 : -1] = 2

# Bottom wall shelves (touching wall, but avoiding entrance)
if entrance_start > 1 + perimeter_shelf_depth:
    # Left of entrance
    layout[-perimeter_shelf_depth - 1 : -1, 1:entrance_start] = 2
if entrance_end < layout.shape[1] - perimeter_shelf_depth - 1:
    # Right of entrance
    layout[-perimeter_shelf_depth - 1 : -1, entrance_end:-1] = 2

# Restore aisles (make sure they are clear)
# Central aisle
layout[side_aisle_width:-side_aisle_width, central_aisle_start:central_aisle_end] = 0
# Cross aisle
layout[
    cross_aisle_y : cross_aisle_y + side_aisle_width, side_aisle_width:-side_aisle_width
] = 0
# Perimeter aisles
layout[1 : 1 + side_aisle_width, 1:-1] = 0  # Top
layout[1:-1, 1 : 1 + side_aisle_width] = 0  # Left
layout[1:-1, -side_aisle_width - 1 : -1] = 0  # Right
layout[-side_aisle_width - 1 : -1, 1:entrance_start] = 0  # Bottom left
layout[-side_aisle_width - 1 : -1, entrance_end:-1] = 0  # Bottom right

# Create checkout area near entrance
checkout_depth = max(1, round(200 / edge_length))  # 2m deep checkout area
checkout_width = max(1, round(80 / edge_length))  # 80cm wide checkout counters
checkout_start_y = layout.shape[0] - side_aisle_width - checkout_depth

# Place checkout counters on both sides of central aisle
num_checkouts_per_side = 3
checkout_spacing = (central_aisle_start - 1 - side_aisle_width) // (
    num_checkouts_per_side + 1
)

# Clear area in front of checkouts
layout[236:248, 1:248] = 0

# Add

# Left side checkouts
for i in range(num_checkouts_per_side):
    checkout_x = 1 + side_aisle_width + (i + 1) * checkout_spacing
    if checkout_x + checkout_width < central_aisle_start:
        layout[
            checkout_start_y : checkout_start_y + checkout_depth,
            checkout_x : checkout_x + checkout_width,
        ] = -1

# Right side checkouts (mirror)
for i in range(num_checkouts_per_side):
    checkout_x = central_aisle_end + (i + 1) * checkout_spacing
    if checkout_x + checkout_width < layout.shape[1] - side_aisle_width - 1:
        layout[
            checkout_start_y : checkout_start_y + checkout_depth,
            checkout_x : checkout_x + checkout_width,
        ] = -1

print(f"🎯 Layout cohérent généré avec allées élargies:")
print(
    f"   - Allée centrale: {central_aisle_width} cells ({CENTRAL_AISLE_WIDTH_CM}cm) alignée avec l'entrée"
)
print(f"   - Allées secondaires: {side_aisle_width} cells ({SIDE_AISLE_WIDTH_CM}cm)")
print(
    f"   - Allées entre étagères: {inter_shelf_aisle_width} cells ({INTER_SHELF_AISLE_CM}cm) minimum"
)
print(f"   - Blocs d'étagères: {len(all_blocks)} blocs avec allées transversales")
print(f"   - Étagères périphériques: touchent les murs")
print(f"   - Largeur étagères: {shelf_width} cells ({SHELF_WIDTH_CM}cm)")
print(f"   - Longueur étagères: {shelf_length} cells ({SHELF_LENGTH_CM}cm)")
print(f"   - Entrée: {entrance_width} cells ({ENTRANCE_WIDTH_CM}cm)")
print(f"   - Toutes les allées: minimum 4 cases de large pour navigation optimale")

# Count cell types for verification
unique, counts = np.unique(layout, return_counts=True)
cell_stats = dict(zip(unique, counts))
print(f"📊 Statistiques des cellules:")
for cell_type, count in cell_stats.items():
    if cell_type == 0:
        print(f"   - Zones navigables (0): {count} cellules")
    elif cell_type == 2:
        print(f"   - Rayons (2): {count} cellules")
    elif cell_type == -1:
        print(f"   - Obstacles (-1): {count} cellules")
    elif cell_type == 1:
        print(f"   - POI (1): {count} cellules")

# Calculate layout hash for filename
layout_hash = calculate_layout_hash(layout, edge_length)

# Save grid with metadata using the same process as grid editor
filepath, _ = save_grid_with_metadata(
    grid=layout,
    edge_length=edge_length,
    zones={},  # No zones for this generated layout
    output_dir="../../api_navimall/assets",
    filename_prefix=layout_hash,  # Use hash as filename
    include_timestamp=False,  # Don't include timestamp, just use hash
)

print(
    f"\n✅ Layout de supermarché généré et sauvegardé dans '{os.path.basename(filepath)}'"
)
print(f"🔑 Hash du layout: {layout_hash}")
print(f"📏 Dimensions: {layout.shape}, edge_length: {edge_length} cm")
