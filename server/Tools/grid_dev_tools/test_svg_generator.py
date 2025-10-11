#!/usr/bin/env python3
"""
Test script for LayoutSVGGenerator - demonstrates SVG generation from .h5 layouts
"""

import os
import sys
import glob

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from api_navimall.layout_svg_generator import (
    LayoutSVGGenerator,
    generate_svg_from_h5,
)


def test_svg_generation():
    """Test SVG generation with available .h5 files"""

    # Look for .h5 files in assets directory
    assets_dir = "../../"
    h5_files = glob.glob(os.path.join(assets_dir, "*.h5"))

    if not h5_files:
        print("❌ No .h5 files found in assets directory")
        return

    print(f"🔍 Found {len(h5_files)} .h5 files:")
    for file in h5_files:
        print(f"   - {os.path.basename(file)}")

    # Get the most recent .h5 file based on modification time
    input_h5 = max(h5_files, key=os.path.getmtime)
    print(f"\n🎨 Generating SVG from: {os.path.basename(input_h5)}")

    # Create output directory
    output_dir = "../../api_navimall/assets/svg_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate output filename
    base_name = os.path.splitext(os.path.basename(input_h5))[0]
    output_svg = os.path.join(output_dir, f"{base_name}_layout.svg")

    try:
        # Generate SVG using the convenience function
        stats = generate_svg_from_h5(input_h5, output_svg, include_metadata=True)

        print("✅ SVG generation completed successfully!")
        print(f"📄 SVG file: {stats['svg_path']}")
        print(
            f"📐 SVG size: {stats['svg_size_cm'][0]:.1f}x{stats['svg_size_cm'][1]:.1f} cm"
        )
        print(f"🧩 Grid elements: {stats['grid_elements']}")
        print(f"🏷️  Zones: {stats['zones_count']}")
        print(f"✨ Animated elements: {stats['animation_elements']}")

        if stats["metadata_path"]:
            print(f"📊 Metadata: {stats['metadata_path']}")

        return True

    except Exception as e:
        print(f"❌ Error generating SVG: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_custom_generator():
    """Test using LayoutSVGGenerator class directly with custom settings"""

    # Look for a specific layout file
    test_file = "../../default_layout.h5"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False

    print(f"🧪 Testing custom generator with: {os.path.basename(test_file)}")

    # Create custom generator with modified settings
    generator = LayoutSVGGenerator()

    # Customize animation settings
    generator.animation_duration = 1.2  # Slower animations
    generator.stagger_delay = 0.15  # More delay between elements

    # Customize colors for a different theme
    generator.cell_colors[2]["fill"] = "#FF7043"  # Orange shelves
    generator.zone_colors = [
        "rgba(255, 107, 129, 0.25)",  # Pink
        "rgba(121, 85, 198, 0.25)",  # Purple
        "rgba(255, 183, 77, 0.25)",  # Orange
        "rgba(76, 201, 240, 0.25)",  # Light Blue
    ]

    # Generate SVG
    output_dir = "../../api_navimall/assets/svg_output"
    output_svg = os.path.join(output_dir, "custom_theme_layout.svg")

    try:
        stats = generator.load_and_generate_svg(
            test_file, output_svg, include_metadata=True
        )

        print("✅ Custom SVG generation completed!")
        print(f"📄 Custom SVG: {stats['svg_path']}")
        print(f"⚙️  Animation duration: {generator.animation_duration}s")
        print(f"⏱️  Stagger delay: {generator.stagger_delay}s")

        return True

    except Exception as e:
        print(f"❌ Error with custom generator: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🎨 LayoutSVGGenerator Test Suite")
    print("=" * 50)

    # Test 1: Basic SVG generation
    print("\n📝 Test 1: Basic SVG Generation")
    test1_result = test_svg_generation()

    # Test 2: Custom generator settings
    print("\n📝 Test 2: Custom Generator Settings")
    test2_result = test_custom_generator()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Test 1 (Basic): {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Test 2 (Custom): {'✅ PASS' if test2_result else '❌ FAIL'}")

    if test1_result and test2_result:
        print("\n🎉 All tests passed! SVG generation is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Open the generated SVG files in a web browser")
        print("   2. Check the animation effects")
        print("   3. Verify the interactive hover effects")
        print("   4. Review the metadata JSON files")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
