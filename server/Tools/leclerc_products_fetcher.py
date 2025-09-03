from bs4 import BeautifulSoup
import json
import re
import json
from pathlib import Path


class LeclercProductsFetcher:
    """
    1 - Copy Leclerc website catalogues's html using the inspector and the copy(document.documentElement.outerHTML) command from the console.
    2 - Paste the copied HTML into a file named "scrapped.html".
    3 - Use fetch to extract product information from "scrapped.html" and save it to "products.json".

    Returns:
        _type_: _description_
    """

    @staticmethod
    def extract_price(product_div):
        """Extrait le prix depuis un div produit, en utilisant aria-label ou les balises p."""
        if not product_div:
            return None

        # Essayer d'extraire le prix depuis l'attribut aria-label
        aria_label = product_div.get("aria-label", "")
        match = re.search(r"(\d+[,\.]\d{2})", aria_label)
        if match:
            return float(match.group(1).replace(",", "."))

        # Sinon, tenter de récupérer depuis les balises p
        deci_tag = product_div.find("p", class_="price-deci")
        cents_tag = product_div.find("p", class_="price-cents")
        if deci_tag and cents_tag:
            price_str = (
                deci_tag.text.strip() + "." + cents_tag.text.strip().replace(",", "")
            )
            try:
                return float(price_str)
            except ValueError:
                return None
        return None

    def fetch_products(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        articles = []

        # Trouver tous les containers de produit
        product_cases = soup.find_all("div", id="product-case")
        for case in product_cases:
            product = {}

            # Nom et marque
            brand_tag = case.find("h3", class_="brand")
            product["brand"] = brand_tag.text.strip() if brand_tag else None

            title_tag = case.find("h4", class_="p-title")
            product["title"] = title_tag.text.strip() if title_tag else None
            if not product["title"]:
                continue  # if title is empty don't add the product

            # Image
            img_tag = case.find("img", id="product_img")
            product["image_url"] = img_tag["src"] if img_tag else None

            # Packaging Type
            packaging_type_div = case.find("div", class_="PackagingType")
            product["packaging_type"] = (
                packaging_type_div.text.strip() if packaging_type_div else None
            )

            if product["packaging_type"] == "Le 1er produit":
                product["packaging_type"] = None

            # Prix des produits
            first_product_div = case.find("div", id="first-product")
            second_product_div = case.find("div", id="second-product")

            product["first_product_price"] = LeclercProductsFetcher.extract_price(
                first_product_div
            )
            product["second_product_price"] = LeclercProductsFetcher.extract_price(
                second_product_div
            )

            # Prix au kilo si disponible
            packaging_div = case.find("div", id="packaging-price")
            if packaging_div:
                match = re.search(
                    r"(\d+[,\.]\d{2})", packaging_div.get("aria-label", "")
                )
                product["price_per_measurement_unit"] = (
                    float(match.group(1).replace(",", ".")) if match else None
                )
            else:
                product["price_per_measurement_unit"] = None

            articles.append(product)

        return articles

    @staticmethod
    def remove_duplicates(products):
        """Remove duplicate products based on title and brand.
        Returns:
            tuple: (unique_products, removed_count)
        """
        seen = set()
        unique_products = []
        initial_count = len(products)

        for product in products:
            identifier = (product["title"], product["brand"])
            if identifier not in seen:
                seen.add(identifier)
                unique_products.append(product)

        removed_count = initial_count - len(unique_products)
        return unique_products, removed_count

    @staticmethod
    def run(html_path="assets/scrapped.html", json_path="assets/products.json"):
        products = LeclercProductsFetcher.fetch_products(html_path)
        file_path = Path(json_path)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                existing_products = json.load(f)
            existing_products.extend(products)
        else:
            existing_products = products

        unique_products, removed_count = LeclercProductsFetcher.remove_duplicates(
            existing_products
        )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(unique_products, f, ensure_ascii=False, indent=4)

        print(f"Added products from path {html_path}:")
        print(f"Total products fetched: {len(products)}")
        print(f"Removed {removed_count} duplicate products.")
        print(f"Unique products count: {len(unique_products)}")
