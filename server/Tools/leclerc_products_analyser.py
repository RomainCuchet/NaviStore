import json
from collections import Counter


class LeclercProductsAnalyser:

    @staticmethod
    def display_product_stats(products, is_analyse_categories=False):
        if not products:
            print("No products available.")
            return

        total_products = len(products)
        brands = set(p["brand"] for p in products if p["brand"])

        # Averages calculated only on valid products
        avg_first_price = (
            sum(
                p["first_product_price"]
                for p in products
                if p["first_product_price"] is not None
            )
            / total_products
        )
        avg_second_price = (
            sum(
                p["second_product_price"]
                for p in products
                if p["second_product_price"] is not None
            )
            / total_products
        )

        min_first_price = min(
            p["first_product_price"]
            for p in products
            if p["first_product_price"] is not None
        )
        max_first_price = max(
            p["first_product_price"]
            for p in products
            if p["first_product_price"] is not None
        )
        avg_price_per_unit = (
            sum(
                p["price_per_measurement_unit"]
                for p in products
                if p["price_per_measurement_unit"] is not None
            )
            / total_products
        )

        print("=== Product Stats ===")
        print(f"Total products: {total_products}")
        print(f"Total unique brands: {len(brands)}")
        print(f"Average price per measurement unit: €{avg_price_per_unit:.2f}")
        print(f"Average first product price: €{avg_first_price:.2f}")
        print(f"Average second product price: €{avg_second_price:.2f}")
        print(f"Lowest first product price: €{min_first_price:.2f}")
        print(f"Highest first product price: €{max_first_price:.2f}")

        if is_analyse_categories:

            categories = [p.get("category", "default") for p in products]
            counter = Counter(categories)

            print("\n=== Category Stats ===")
            print(f"Total categories: {len(counter)}")
            for cat, count in counter.most_common():
                print(f"- {cat}: {count} product(s)")

    @staticmethod
    def run(json_path="assets/products.json"):
        """Load products from a JSON file and display stats."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                products = json.load(f)
            LeclercProductsAnalyser.display_product_stats(products)
        except FileNotFoundError:
            print(f"File {json_path} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {json_path}.")
