import json
from anyio import Path
from collections import defaultdict
import random

from api_navimall.path_optimization.utils import (
    load_layout_from_h5,
    grid_to_real_world_coords,
)


class ProductsManager:
    def __init__(
        self,
        products_json_path="api_navimall/assets/json/products.json",
        data_store_path="api_navimall/assets/json/data_store.json",
    ):
        self.json_path = products_json_path
        self.data_store_path = data_store_path

        self.products = self.__load_existing_products()
        self.next_product_id_at_init = self.__fetch_next_product_id()
        self.next_product_id = self.next_product_id_at_init

        if len(self.products) >= self.next_product_id:
            raise ValueError(
                "The next_product_id is less than or equal to the number of existing products, there is an issue in the data store or products file."
            )

        self.products_titles_id_brand_index = defaultdict(list)
        for p in self.products:
            if "id" in p:
                self.products_titles_id_brand_index[
                    f"{p['title']}-{p['brand']}"
                ].append(p["id"])

        self.products_index_by_id = {p["id"]: p for p in self.products if "id" in p}

    # =====================================================
    # SECTION: Private methods
    # =====================================================

    def __load_existing_products(self):
        file_path = Path(self.json_path)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                products = json.load(f)
                return products
        else:
            return []

    def __fetch_next_product_id(self):
        if not Path(self.data_store_path).exists():
            with open(self.data_store_path, "w", encoding="utf-8") as f:
                json.dump({"next_id": 1}, f)
                next_product_id = 1
            return 1
        with open(self.data_store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            next_product_id = data.get("next_product_id")
        return next_product_id

    def __is_existing_product(self, product):
        """Check if a product already exists in the products list based on title and brand."""
        return (
            f"{product.get('title')}-{product.get('brand')}"
            in self.products_titles_id_brand_index
        )

    def __save_products(self):
        if self.next_product_id < self.next_product_id_at_init:
            raise ValueError(
                "next_product_id cannot be less than its initial value, there is an issue in the code logic."
            )
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.products, f, ensure_ascii=False, indent=4)

    def __update_data_store(self, key: str, value):
        try:
            with open(self.data_store_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data[key] = value
            with open(self.data_store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(
                f"New next_product_id ({self.next_product_id}) in {self.data_store_path}."
            )
        except FileNotFoundError:
            with open(self.data_store_path, "w", encoding="utf-8") as f:
                json.dump({"next_product_id": self.next_product_id}, f, indent=4)

    # =====================================================
    # SECTION: Public methods
    # =====================================================

    def summary(self):
        return {
            "total_products": len(self.products),
            "next_product_id": self.next_product_id,
            "initial_next_product_id": self.next_product_id_at_init,
            "data_store_path": self.data_store_path,
            "products_json_path": self.json_path,
            "duplicate_products_count": len(self.get_duplicates_ids()),
        }

    def get_product_by_id(self, product_id):
        return self.products_index_by_id.get(product_id) if product_id else None

    def get_products_by_ids(self, product_ids):
        return [
            self.products_index_by_id.get(pid)
            for pid in product_ids
            if pid in self.products_index_by_id
        ]

    def get_duplicates_ids(self):
        """Get duplicate product ids. Two products are considered duplicates if they have the same title and brand.

        Returns:
            dict: A dictionary with titles as keys and a list of tuples (id, brand) as values.
        """

        resultat_filtre = {
            title: ids
            for title, ids in self.products_titles_id_brand_index.items()
            if len(ids) > 1
        }

        return resultat_filtre

    def fetch_products_from_leclerc(self, html_file_path):
        from tools.leclerc_products_fetcher import LeclercProductsFetcher

        products = LeclercProductsFetcher.fetch_products(html_file_path)

        count_added_products = 0

        for product in products:
            if not self.__is_existing_product(product):
                product["id"] = self.next_product_id
                self.products.append(product)
                self.products_titles_id_brand_index[
                    f"{product['title']}-{product['brand']}"
                ].append(product["id"])
                self.products_index_by_id[product["id"]] = product
                self.next_product_id += 1
                count_added_products += 1
        if count_added_products > 0:
            print(f"Added {count_added_products} new products to {self.json_path}.")
            self.__save_products()
            self.__update_data_store("next_product_id", self.next_product_id)
        else:
            print(f"No new products to add from {html_file_path} to {self.json_path}.")
        return products

    def update_categories(self) -> set:
        categories = set()
        for product in self.products:
            if "category" in product and product["category"]:
                categories.add(product["category"])
        self.__update_data_store("categories", list(categories))
        return categories

    def set_test_positions(self, layout_path):

        def random_position(free_cells):

            for product in self.products:
                pos = random.choice(free_cells)
                if pos:
                    product["position"] = pos
            print(
                f"Assigned random positions to {len(self.products)} products in the layout."
            )

        def by_category():
            pass  # TODO: implement this method later

        layout, edge_length, _ = load_layout_from_h5(layout_path)
        layout_height, layout_width = layout.shape

        free_cells = []
        for i in range(layout_height):
            for j in range(layout_width):
                if layout[i, j] == 0:
                    # Check all adjacent cells (up, down, left, right)
                    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ni, nj = i + di, j + dj
                        if (
                            0 <= ni < layout_height
                            and 0 <= nj < layout_width
                            and layout[ni, nj] == 2
                        ):
                            free_cells.append((i, j))
                            break

        if not free_cells:
            raise ValueError("No free cells available for product placement.")

        random_position(free_cells)

        # Convert grid positions to real-world coordinates (in cm) using utils
        grid_points = []
        product_indices = []
        for idx, product in enumerate(self.products):
            if "position" in product and product["position"] is not None:
                i, j = product["position"]
                grid_points.append((i, j))
                product_indices.append(idx)

        if grid_points:
            import numpy as np

            grid_arr = np.array(grid_points, dtype=float).reshape(-1, 2)
            # Swap (row, col) -> (col, row) to align real-world x with column index
            grid_arr_swapped = grid_arr[:, [1, 0]]
            real_arr_swapped = grid_to_real_world_coords(grid_arr_swapped, edge_length)
            real_points = real_arr_swapped.tolist()

            for idx, real_pos in zip(product_indices, real_points):
                self.products[idx]["position"] = tuple(real_pos)

        self.__save_products()
