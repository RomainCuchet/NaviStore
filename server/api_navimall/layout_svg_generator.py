import h5py
import numpy as np
import json
import os
import xxhash
import datetime
from typing import Tuple, Optional, List, Dict, Any
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom

from api_navimall.path_optimization.utils import load_layout_from_h5, Zone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LayoutSVGGenerator:
    """
    Transforms .h5 layout files into interactive, animated SVG supermarket maps
    optimized for Flutter app integration with modern light-mode design.
    """

    def __init__(self):
        self.cell_colors = {
            0: {"fill": "none", "name": "navigable"},  # Transparent navigable areas
            1: {
                "fill": "hsl(230, 80%, 50%)",
                "name": "poi",
            },  # Bleu vif harmonieux avec seed color
            -1: {"fill": "#9E9E9E", "name": "obstacle"},  # Gray obstacles
            2: {"fill": "#8D6E63", "name": "shelf"},  # Brown shelves
        }

        self.zone_colors = [
            "hsla(230, 70%, 60%, 0.25)",  # Bleu principal harmonieux
            "hsla(210, 50%, 70%, 0.25)",  # Bleu clair
            "hsla(250, 60%, 65%, 0.25)",  # Bleu-violet
            "hsla(190, 55%, 75%, 0.25)",  # Bleu cyan
            "hsla(270, 40%, 70%, 0.25)",  # Violet clair
            "hsla(200, 45%, 65%, 0.25)",  # Bleu gris
            "hsla(220, 50%, 75%, 0.25)",  # Bleu pastel
            "hsla(240, 35%, 80%, 0.25)",  # Bleu très clair
        ]

        self.animation_duration = 0.8  # seconds
        self.stagger_delay = 0.1  # seconds between element animations

    def load_and_generate_svg(
        self, h5_filename: str, output_svg_path: str, include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Main method to load .h5 file and generate interactive SVG.

        Args:
            h5_filename: Path to the .h5 layout file
            output_svg_path: Path where SVG will be saved
            include_metadata: Whether to include JSON metadata

        Returns:
            Dictionary with generation metadata and statistics
        """
        logger.info(f"🎨 Starting SVG generation from {h5_filename}")

        # Load layout data using the reference function
        layout_array, edge_length, zones = load_layout_from_h5(h5_filename)

        # Calculate SVG dimensions
        height, width = layout_array.shape
        svg_width = width * edge_length
        svg_height = height * edge_length

        logger.info(f"📐 Layout: {width}x{height} cells, {edge_length}cm/cell")
        logger.info(f"📏 SVG size: {svg_width}x{svg_height}cm")

        # Create SVG root element
        svg_root = self._create_svg_root(svg_width, svg_height)

        # Add definitions for animations and patterns
        defs = self._create_definitions(svg_root)

        # Create layer groups
        layers = self._create_layer_structure(svg_root)

        # Generate grid elements
        grid_stats = self._generate_grid_elements(layout_array, edge_length, layers)

        # Generate zone elements
        zone_stats = self._generate_zone_elements(zones, edge_length, layers)

        # Add animations
        self._add_reveal_animations(svg_root, grid_stats, zone_stats)

        # Save SVG to file
        self._save_svg(svg_root, output_svg_path)

        # Generate metadata if requested
        metadata = {}
        if include_metadata:
            metadata = self._generate_metadata(
                layout_array, edge_length, zones, grid_stats, zone_stats
            )
            metadata_path = output_svg_path.replace(".svg", "_metadata.json")
            self._save_metadata(metadata, metadata_path)

        generation_stats = {
            "svg_path": output_svg_path,
            "svg_size_cm": (svg_width, svg_height),
            "grid_elements": grid_stats["total_elements"],
            "zones_count": len(zones),
            "animation_elements": grid_stats["animated_elements"]
            + zone_stats["animated_elements"],
            "metadata_path": metadata_path if include_metadata else None,
        }

        logger.info(f"✅ SVG generated successfully: {output_svg_path}")
        return generation_stats

    def _create_svg_root(self, width: float, height: float) -> ET.Element:
        """Create SVG root element with proper namespaces and viewBox."""
        svg = ET.Element("svg")
        svg.set("xmlns", "http://www.w3.org/2000/svg")
        svg.set("xmlns:xlink", "http://www.w3.org/1999/xlink")
        svg.set("viewBox", f"0 0 {width} {height}")
        svg.set("width", f"{width}")
        svg.set("height", f"{height}")
        svg.set(
            "style",
            'background-color: hsl(230, 20%, 96%); font-family: "Roboto", sans-serif;',
        )

        # Add title and description for accessibility
        title = ET.SubElement(svg, "title")
        title.text = "Interactive Supermarket Layout"

        desc = ET.SubElement(svg, "desc")
        desc.text = "Animated SVG representation of supermarket layout with zones and navigation paths"

        return svg

    def _create_definitions(self, svg_root: ET.Element) -> ET.Element:
        """Create SVG definitions for gradients, patterns, and animations."""
        defs = ET.SubElement(svg_root, "defs")

        # Create modern gradient for shelves (inspired by the provided SVG)
        shelf_gradient = ET.SubElement(
            defs,
            "linearGradient",
            id="shelfGradient",
            gradientTransform="rotate(45, 0.5, 0.5)",
        )

        # Gradient stops similar to the example (purple/violet theme)
        stop1 = ET.SubElement(shelf_gradient, "stop")
        stop1.set("stop-color", "hsl(265, 55%, 30%)")  # Dark purple
        stop1.set("offset", "0")

        stop2 = ET.SubElement(shelf_gradient, "stop")
        stop2.set("stop-color", "hsl(265, 60%, 52%)")  # Light purple
        stop2.set("offset", "1")

        # Alternative gradient for variety
        shelf_gradient2 = ET.SubElement(
            defs,
            "linearGradient",
            id="shelfGradient2",
            gradientTransform="rotate(-45, 0.5, 0.5)",
        )

        stop3 = ET.SubElement(shelf_gradient2, "stop")
        stop3.set("stop-color", "hsl(200, 50%, 40%)")  # Dark blue
        stop3.set("offset", "0")

        stop4 = ET.SubElement(shelf_gradient2, "stop")
        stop4.set("stop-color", "hsl(200, 60%, 60%)")  # Light blue
        stop4.set("offset", "1")

        # Create POI marker pattern
        poi_marker = ET.SubElement(defs, "g", id="poi-marker")
        circle = ET.SubElement(poi_marker, "circle")
        circle.set("r", "8")
        circle.set("fill", "hsl(230, 80%, 50%)")  # Bleu vif
        circle.set("stroke", "hsl(230, 90%, 35%)")  # Bleu foncé
        circle.set("stroke-width", "2")

        # Add inner dot
        inner_circle = ET.SubElement(poi_marker, "circle")
        inner_circle.set("r", "3")
        inner_circle.set("fill", "#FFFFFF")

        return defs

    def _create_layer_structure(self, svg_root: ET.Element) -> Dict[str, ET.Element]:
        """Create organized layer structure for different element types."""
        layers = {}

        # Background layer
        layers["background"] = ET.SubElement(svg_root, "g", id="background-layer")

        # Grid elements layer
        layers["grid"] = ET.SubElement(svg_root, "g", id="grid-layer")

        # Obstacles layer
        layers["obstacles"] = ET.SubElement(svg_root, "g", id="obstacles-layer")

        # Shelves layer (visible by default - Flutter strips style/script)
        shelves_layer = ET.SubElement(svg_root, "g", id="shelves-layer")
        shelves_layer.set("opacity", "1")
        layers["shelves"] = shelves_layer

        # POI layer
        layers["poi"] = ET.SubElement(svg_root, "g", id="poi-layer")

        # Zones layer (initially hidden; can be toggled later if needed)
        zones_layer = ET.SubElement(svg_root, "g", id="zones-layer")
        zones_layer.set("opacity", "0")
        layers["zones"] = zones_layer

        # Annotations layer (for labels and UI elements)
        layers["annotations"] = ET.SubElement(svg_root, "g", id="annotations-layer")

        return layers

    def _generate_grid_elements(
        self,
        layout_array: np.ndarray,
        edge_length: float,
        layers: Dict[str, ET.Element],
    ) -> Dict[str, Any]:
        """Generate SVG elements as contiguous shapes for modern design."""
        height, width = layout_array.shape
        stats = {"total_elements": 0, "animated_elements": 0, "cell_counts": {}}

        # Count cell types - convert numpy int64 to regular int for JSON serialization
        for cell_type in [0, 1, -1, 2]:
            stats["cell_counts"][cell_type] = int(np.sum(layout_array == cell_type))

        logger.info(f"📊 Grid stats: {stats['cell_counts']}")

        # Generate contiguous shapes for each cell type
        # Obstacles (-1) - dark shapes without gradients
        obstacle_shapes = self._find_contiguous_regions(layout_array, -1)
        for i, shape in enumerate(obstacle_shapes):
            self._create_contiguous_obstacle(layers["obstacles"], shape, edge_length, i)
            stats["total_elements"] += 1

        # Shelves (2) - simple shapes without animation
        shelf_shapes = self._find_contiguous_regions(layout_array, 2)
        logger.info(f"🏪 Found {len(shelf_shapes)} shelf regions")
        for i, shape in enumerate(shelf_shapes):
            gradient_id = "shelfGradient" if i % 2 == 0 else "shelfGradient2"
            self._create_contiguous_shelf(
                layers["shelves"], shape, edge_length, i, gradient_id
            )
            stats["total_elements"] += 1
            # stats["animated_elements"] += 1  # Plus d'animation pour les étagères

        # POI (1) - individual markers
        poi_positions = np.where(layout_array == 1)
        for y, x in zip(poi_positions[0], poi_positions[1]):
            self._create_poi_element(
                layers["poi"], x * edge_length, y * edge_length, edge_length, x, y
            )
            stats["total_elements"] += 1

        # Navigable areas (0) remain transparent (no elements needed)

        return stats

    def _find_contiguous_regions(
        self, layout_array: np.ndarray, cell_type: int
    ) -> List[List[Tuple[int, int]]]:
        """Find all contiguous regions of the same cell type using flood fill."""
        height, width = layout_array.shape
        visited = np.zeros((height, width), dtype=bool)
        regions = []

        def flood_fill(start_y, start_x):
            """Flood fill to find connected component."""
            stack = [(start_y, start_x)]
            region = []

            while stack:
                y, x = stack.pop()
                if (
                    y < 0
                    or y >= height
                    or x < 0
                    or x >= width
                    or visited[y, x]
                    or layout_array[y, x] != cell_type
                ):
                    continue

                visited[y, x] = True
                region.append((y, x))

                # Add 4-connected neighbors
                stack.extend([(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)])

            return region

        # Find all regions
        for y in range(height):
            for x in range(width):
                if not visited[y, x] and layout_array[y, x] == cell_type:
                    region = flood_fill(y, x)
                    if region:
                        regions.append(region)

        return regions

    def _create_contiguous_obstacle(
        self,
        layer: ET.Element,
        shape: List[Tuple[int, int]],
        edge_length: float,
        shape_id: int,
    ) -> None:
        """Create a contiguous obstacle shape with Flutter theme colors."""
        if not shape:
            return

        # Create path data for the shape
        path_data = self._create_path_from_cells(shape, edge_length)

        obstacle_path = ET.SubElement(layer, "path", id=f"obstacle_shape_{shape_id}")
        obstacle_path.set("d", path_data)
        obstacle_path.set(
            "fill", "hsl(230, 50%, 20%)"
        )  # Bleu très foncé harmonieux avec seed color
        obstacle_path.set("stroke", "hsl(230, 60%, 15%)")  # Bordure encore plus foncée
        obstacle_path.set("stroke-width", "1")
        obstacle_path.set("opacity", "0.85")
        obstacle_path.set("class", "obstacle-shape")

    def _create_contiguous_shelf(
        self,
        layer: ET.Element,
        shape: List[Tuple[int, int]],
        edge_length: float,
        shape_id: int,
        gradient_id: str,
    ) -> None:
        """Create a contiguous shelf shape with simple styling (no animation)."""
        if not shape:
            logger.warning(f"⚠️  Empty shape for shelf {shape_id}")
            return

        # Create path data for the shape
        path_data = self._create_path_from_cells(shape, edge_length)

        if not path_data:
            logger.warning(f"⚠️  No path data generated for shelf {shape_id}")
            return

        # Simple group without animation class
        shelf_group = ET.SubElement(layer, "g", id=f"shelf_shape_{shape_id}")
        shelf_group.set("class", "shelf-shape")
        # Pas d'opacity=0, visible immédiatement

        shelf_path = ET.SubElement(shelf_group, "path")
        shelf_path.set("d", path_data)
        shelf_path.set(
            "fill", "hsl(230, 30%, 75%)"
        )  # Bleu clair harmonieux avec le thème Flutter
        shelf_path.set("stroke", "hsl(230, 40%, 60%)")  # Bordure bleu moyen
        shelf_path.set("stroke-width", "1")
        shelf_path.set("opacity", "0.9")

    def _create_path_from_cells(
        self, cells: List[Tuple[int, int]], edge_length: float
    ) -> str:
        """Create SVG path data from a list of grid cells, tracing the actual boundary."""
        if not cells:
            return ""

        # Convert to set for fast lookup
        cell_set = set(cells)

        # For simple rectangular shapes, use the old method
        if self._is_rectangular_region(cells):
            return self._create_rectangular_path(cells, edge_length)

        # For complex shapes, trace the boundary
        return self._trace_boundary_path(cells, edge_length)

    def _is_rectangular_region(self, cells: List[Tuple[int, int]]) -> bool:
        """Check if the region is a simple rectangle."""
        if not cells:
            return False

        min_y = min(cell[0] for cell in cells)
        max_y = max(cell[0] for cell in cells)
        min_x = min(cell[1] for cell in cells)
        max_x = max(cell[1] for cell in cells)

        expected_count = (max_y - min_y + 1) * (max_x - min_x + 1)
        return len(cells) == expected_count

    def _create_rectangular_path(
        self, cells: List[Tuple[int, int]], edge_length: float
    ) -> str:
        """Create a simple rectangular path with rounded corners."""
        min_y = min(cell[0] for cell in cells)
        max_y = max(cell[0] for cell in cells)
        min_x = min(cell[1] for cell in cells)
        max_x = max(cell[1] for cell in cells)

        x = min_x * edge_length
        y = min_y * edge_length
        width = (max_x - min_x + 1) * edge_length
        height = (max_y - min_y + 1) * edge_length

        # Create rounded rectangle path
        radius = min(edge_length * 0.1, 8)

        return f"""M {x + radius} {y}
        L {x + width - radius} {y}
        Q {x + width} {y} {x + width} {y + radius}
        L {x + width} {y + height - radius}
        Q {x + width} {y + height} {x + width - radius} {y + height}
        L {x + radius} {y + height}
        Q {x} {y + height} {x} {y + height - radius}
        L {x} {y + radius}
        Q {x} {y} {x + radius} {y}
        Z""".replace(
            "\n", " "
        ).strip()

    def _trace_boundary_path(
        self, cells: List[Tuple[int, int]], edge_length: float
    ) -> str:
        """Trace the actual boundary of a complex shape using marching squares approach."""
        if not cells:
            return ""

        cell_set = set(cells)

        # Find boundary points by checking edges of cells
        boundary_segments = []

        for y, x in cells:
            cell_x = x * edge_length
            cell_y = y * edge_length

            # Check each edge of the cell
            # Top edge
            if (y - 1, x) not in cell_set:
                boundary_segments.append(
                    ("H", cell_x, cell_y, cell_x + edge_length, cell_y)
                )

            # Right edge
            if (y, x + 1) not in cell_set:
                boundary_segments.append(
                    (
                        "V",
                        cell_x + edge_length,
                        cell_y,
                        cell_x + edge_length,
                        cell_y + edge_length,
                    )
                )

            # Bottom edge
            if (y + 1, x) not in cell_set:
                boundary_segments.append(
                    (
                        "H",
                        cell_x + edge_length,
                        cell_y + edge_length,
                        cell_x,
                        cell_y + edge_length,
                    )
                )

            # Left edge
            if (y, x - 1) not in cell_set:
                boundary_segments.append(
                    ("V", cell_x, cell_y + edge_length, cell_x, cell_y)
                )

        if not boundary_segments:
            return self._create_rectangular_path(cells, edge_length)

        # Sort and connect boundary segments to form a path
        path_parts = []

        # Start with the first segment
        current_segment = boundary_segments[0]
        path_parts.append(f"M {current_segment[1]} {current_segment[2]}")
        path_parts.append(f"L {current_segment[3]} {current_segment[4]}")

        used_segments = {0}
        current_end = (current_segment[3], current_segment[4])

        # Connect remaining segments
        while len(used_segments) < len(boundary_segments):
            found_next = False

            for i, segment in enumerate(boundary_segments):
                if i in used_segments:
                    continue

                # Check if this segment connects to current end
                if (
                    abs(segment[1] - current_end[0]) < 0.1
                    and abs(segment[2] - current_end[1]) < 0.1
                ):
                    path_parts.append(f"L {segment[3]} {segment[4]}")
                    current_end = (segment[3], segment[4])
                    used_segments.add(i)
                    found_next = True
                    break
                elif (
                    abs(segment[3] - current_end[0]) < 0.1
                    and abs(segment[4] - current_end[1]) < 0.1
                ):
                    path_parts.append(f"L {segment[1]} {segment[2]}")
                    current_end = (segment[1], segment[2])
                    used_segments.add(i)
                    found_next = True
                    break

            if not found_next:
                break

        path_parts.append("Z")
        return " ".join(path_parts)

    def _create_poi_element(
        self,
        layer: ET.Element,
        x: float,
        y: float,
        size: float,
        grid_x: int,
        grid_y: int,
    ) -> None:
        """Create POI marker element."""
        poi_group = ET.SubElement(layer, "g", id=f"poi_{grid_x}_{grid_y}")
        poi_group.set("class", "poi-marker")

        # Center the POI marker in the cell
        center_x = x + size / 2
        center_y = y + size / 2

        # Outer circle
        outer_circle = ET.SubElement(poi_group, "circle")
        outer_circle.set("cx", str(center_x))
        outer_circle.set("cy", str(center_y))
        outer_circle.set("r", str(min(size * 0.3, 12)))
        outer_circle.set("fill", "hsl(230, 80%, 50%)")  # Bleu vif
        outer_circle.set("stroke", "hsl(230, 90%, 35%)")  # Bleu foncé
        outer_circle.set("stroke-width", "2")
        outer_circle.set("opacity", "0.9")

        # Inner highlight
        inner_circle = ET.SubElement(poi_group, "circle")
        inner_circle.set("cx", str(center_x))
        inner_circle.set("cy", str(center_y))
        inner_circle.set("r", str(min(size * 0.15, 6)))
        inner_circle.set("fill", "#FFFFFF")
        inner_circle.set("opacity", "0.8")

    def _generate_zone_elements(
        self, zones: Dict[str, Zone], edge_length: float, layers: Dict[str, ET.Element]
    ) -> Dict[str, Any]:
        """Generate SVG elements for semantic zones."""
        stats = {"animated_elements": 0, "total_zones": len(zones)}

        for i, (zone_id, zone) in enumerate(zones.items()):
            color = self.zone_colors[i % len(self.zone_colors)]
            self._create_zone_element(
                layers["zones"], zone_id, zone, edge_length, color
            )
            stats["animated_elements"] += 1

        logger.info(f"🏷️ Generated {len(zones)} zone elements")
        return stats

    def _create_zone_element(
        self,
        layer: ET.Element,
        zone_id: str,
        zone: Zone,
        edge_length: float,
        color: str,
    ) -> None:
        """Create zone polygon element with animation attributes."""
        zone_group = ET.SubElement(layer, "g", id=f"zone_{zone_id}")
        zone_group.set("class", "zone animated-element")
        zone_group.set("opacity", "0")  # Initially hidden

        # Convert zone points to SVG coordinates
        points_str = ""
        for point in zone.points:
            svg_x = point[0] * edge_length
            svg_y = point[1] * edge_length
            points_str += f"{svg_x},{svg_y} "

        # Create zone polygon
        polygon = ET.SubElement(zone_group, "polygon")
        polygon.set("points", points_str.strip())
        polygon.set("fill", color)
        polygon.set("stroke", color.replace("0.2", "0.6"))  # More opaque border
        polygon.set("stroke-width", "2")
        polygon.set("stroke-dasharray", "4,2")

        # Add zone label
        if zone.points:
            # Calculate centroid for label placement
            centroid_x = sum(p[0] for p in zone.points) / len(zone.points) * edge_length
            centroid_y = sum(p[1] for p in zone.points) / len(zone.points) * edge_length

            label = ET.SubElement(zone_group, "text")
            label.set("x", str(centroid_x))
            label.set("y", str(centroid_y))
            label.set("text-anchor", "middle")
            label.set("dominant-baseline", "middle")
            label.set("font-size", "14")
            label.set("font-weight", "bold")
            label.set("fill", "#333333")
            label.text = zone.name

    def _add_reveal_animations(
        self,
        svg_root: ET.Element,
        grid_stats: Dict[str, Any],
        zone_stats: Dict[str, Any],
    ) -> None:
        """Add CSS animations for cool reveal effects."""
        style = ET.SubElement(svg_root, "style")
        style.set("type", "text/css")

        css_animations = f"""
        /* Base animation keyframes */
        @keyframes fadeInScale {{
            0% {{ opacity: 0; transform: scale(0.8); }}
            50% {{ opacity: 0.5; transform: scale(1.05); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}
        
        @keyframes slideInFromLeft {{
            0% {{ opacity: 0; transform: translateX(-20px); }}
            100% {{ opacity: 1; transform: translateX(0); }}
        }}
        
        @keyframes zoneReveal {{
            0% {{ opacity: 0; transform: scale(0.95) rotate(-1deg); }}
            60% {{ opacity: 0.7; transform: scale(1.02) rotate(0.5deg); }}
            100% {{ opacity: 1; transform: scale(1) rotate(0deg); }}
        }}
        
        /* Element-specific animations */
        .shelf-shape.animated-element {{
            animation: fadeInScale {self.animation_duration}s ease-out forwards;
        }}
        
        .zone.animated-element {{
            animation: zoneReveal {self.animation_duration * 1.2}s ease-out forwards;
        }}
        
        .poi-marker {{
            animation: fadeInScale {self.animation_duration * 0.8}s ease-out forwards;
        }}
        
        /* Staggered animation delays */
        .shelf-shape.animated-element:nth-child(odd) {{
            animation-delay: {self.stagger_delay}s;
        }}
        
        .shelf-shape.animated-element:nth-child(even) {{
            animation-delay: {self.stagger_delay * 2}s;
        }}
        
        .zone.animated-element:nth-child(1) {{ animation-delay: {self.stagger_delay * 3}s; }}
        .zone.animated-element:nth-child(2) {{ animation-delay: {self.stagger_delay * 4}s; }}
        .zone.animated-element:nth-child(3) {{ animation-delay: {self.stagger_delay * 5}s; }}
        .zone.animated-element:nth-child(4) {{ animation-delay: {self.stagger_delay * 6}s; }}
        
        /* Hover effects for interactivity */
        .shelf:hover {{ opacity: 1 !important; transform: scale(1.05); transition: all 0.2s ease; }}
        .zone:hover {{ opacity: 0.8 !important; transition: all 0.3s ease; }}
        .poi-marker:hover {{ transform: scale(1.2); transition: all 0.2s ease; }}
        """

        style.text = css_animations

        # Add trigger script for programmatic animation control
        script = ET.SubElement(svg_root, "script")
        script.set("type", "text/javascript")
        script.text = """
        function revealShelves() {
            const shelves = document.querySelectorAll('#shelves-layer');
            shelves.forEach(layer => layer.style.opacity = '1');
        }
        
        function revealZones() {
            const zones = document.querySelectorAll('#zones-layer');
            zones.forEach(layer => layer.style.opacity = '1');
        }
        
        function revealAll() {
            revealShelves();
            setTimeout(revealZones, 500);
        }
        
        // Auto-start animations after a short delay
        setTimeout(revealAll, 1000);
        """

    def _save_svg(self, svg_root: ET.Element, output_path: str) -> None:
        """Save SVG to file with proper formatting."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Remove unsupported elements for Flutter rendering
        self._strip_unsupported_elements(svg_root)

        # Convert to string with pretty formatting
        rough_string = ET.tostring(svg_root, "unicode")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # Remove extra empty lines
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        formatted_xml = "\n".join(lines)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_xml)

    def _strip_unsupported_elements(self, svg_root: ET.Element) -> None:
        """Remove SVG elements not supported by flutter_svg (<style>, <script>)."""
        unsupported_tags = {"style", "script"}

        for parent in svg_root.iter():
            for child in list(parent):
                tag_name = child.tag.split("}")[-1].lower()
                if tag_name in unsupported_tags:
                    parent.remove(child)

    def _generate_metadata(
        self,
        layout_array: np.ndarray,
        edge_length: float,
        zones: Dict[str, Zone],
        grid_stats: Dict[str, Any],
        zone_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive metadata for the SVG."""
        height, width = layout_array.shape

        metadata = {
            "generation_info": {
                "timestamp": datetime.datetime.now().isoformat(),
                "generator": "LayoutSVGGenerator",
                "version": "1.0.0",
            },
            "layout_specs": {
                "grid_size": [width, height],
                "edge_length_cm": edge_length,
                "total_area_cm2": width * height * edge_length * edge_length,
                "svg_dimensions_cm": [width * edge_length, height * edge_length],
            },
            "element_counts": {
                "total_grid_elements": grid_stats["total_elements"],
                "cell_distribution": grid_stats["cell_counts"],
                "zones": zone_stats["total_zones"],
                "animated_elements": grid_stats["animated_elements"]
                + zone_stats["animated_elements"],
            },
            "zones_metadata": {},
            "animation_config": {
                "duration_seconds": self.animation_duration,
                "stagger_delay_seconds": self.stagger_delay,
                "reveal_sequence": ["shelves", "zones"],
            },
            "styling": {
                "theme": "light_mode",
                "color_palette": {
                    "navigable": "transparent",
                    "poi": "#4CAF50",
                    "obstacle": "#9E9E9E",
                    "shelf": "#8D6E63",
                },
                "zone_colors": self.zone_colors,
            },
        }

        # Add detailed zone metadata
        for zone_id, zone in zones.items():
            zone_area = self._calculate_zone_area(zone.points, edge_length)
            metadata["zones_metadata"][zone_id] = {
                "name": zone.name,
                "points_count": len(zone.points),
                "area_cm2": zone_area,
                "bounds": self._calculate_zone_bounds(zone.points, edge_length),
            }

        return metadata

    def _calculate_zone_area(
        self, points: List[Tuple[float, float]], edge_length: float
    ) -> float:
        """Calculate zone area using shoelace formula."""
        if len(points) < 3:
            return 0.0

        # Convert to real coordinates
        real_points = [(p[0] * edge_length, p[1] * edge_length) for p in points]

        # Shoelace formula
        area = 0.0
        n = len(real_points)
        for i in range(n):
            j = (i + 1) % n
            area += real_points[i][0] * real_points[j][1]
            area -= real_points[j][0] * real_points[i][1]

        return abs(area) / 2.0

    def _calculate_zone_bounds(
        self, points: List[Tuple[float, float]], edge_length: float
    ) -> Dict[str, float]:
        """Calculate bounding box for zone."""
        if not points:
            return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}

        real_points = [(p[0] * edge_length, p[1] * edge_length) for p in points]
        min_x = min(p[0] for p in real_points)
        max_x = max(p[0] for p in real_points)
        min_y = min(p[1] for p in real_points)
        max_y = max(p[1] for p in real_points)

        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
        }

    def _save_metadata(self, metadata: Dict[str, Any], output_path: str) -> None:
        """Save metadata to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Metadata saved to: {output_path}")


# Convenience function for easy usage
def generate_svg_from_h5(
    h5_path: str, output_svg_path: str, include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to generate SVG from .h5 layout file.

    Args:
        h5_filename: Path to the .h5 layout file
        output_svg_path: Path where SVG will be saved
        include_metadata: Whether to generate metadata JSON file

    Returns:
        Dictionary with generation statistics and file paths
    """
    generator = LayoutSVGGenerator()
    return generator.load_and_generate_svg(h5_path, output_svg_path, include_metadata)
