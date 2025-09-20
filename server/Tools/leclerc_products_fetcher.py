from bs4 import BeautifulSoup
import json
import re
import json
from pathlib import Path


class LeclercProductsFetcher:
    """
    1 - Copy Leclerc website catalogues's html using the inspector and the copy(document.documentElement.outerHTML) command from the console.
    If it doesn't work, try copy(document.body.outerHTML)
    2 - Paste the copied HTML into an .html file in the assets folder.
    3 - Use fetch to extract product information from the HTML file.
    4 - The fetch function will return a list of products.

    """

    @staticmethod
    def __extract_price(product_div):
        """Extracts the price from a product div, using aria-label or p tags."""
        if not product_div:
            return None

        # Try to extract the price from the aria-label attribute
        aria_label = product_div.get("aria-label", "")
        match = re.search(r"(\d+[,\.]\d{2})", aria_label)
        if match:
            return float(match.group(1).replace(",", "."))

        # Otherwise, try to get from p tags
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

    @staticmethod
    def __get_category(case):
        """Gets the product category from its parent 'category_xxx'."""
        category_div = case.find_parent("div", id=re.compile(r"^category_"))
        if category_div:
            # Look for category header image
            img_div = category_div.find("div", class_="img_div")
            if img_div:
                img_tag = img_div.find("img")
                if img_tag and img_tag.get("alt"):
                    # Clean 'Rayon XXX' if present
                    alt_text = img_tag["alt"].strip()
                    return re.sub(r"^Rayon\s+", "", alt_text)
        return "default"

    @staticmethod
    def fetch_products(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        articles = []
        product_cases = soup.find_all("div", id="product-case")
        for case in product_cases:
            product = {}

            # Name and brand
            brand_tag = case.find("h3", class_="brand")
            product["brand"] = brand_tag.text.strip() if brand_tag else None

            title_tag = case.find("h4", class_="p-title")
            product["title"] = title_tag.text.strip() if title_tag else None
            if not product["title"]:
                continue

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

            # Price
            first_product_div = case.find("div", id="first-product")
            second_product_div = case.find("div", id="second-product")

            product["first_product_price"] = LeclercProductsFetcher.__extract_price(
                first_product_div
            )
            product["second_product_price"] = LeclercProductsFetcher.__extract_price(
                second_product_div
            )

            # Price per kilo
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

            # Category
            product["category"] = LeclercProductsFetcher.__get_category(case)

            articles.append(product)
            print(f"Fetched {len(articles)} products from {html_path}.")

        return articles
