import requests
import json

API_KEY = "J6PLb4ieglfDuANH0oBWoq9hdEA5fKmH"  # Clé API de test (à ne pas utiliser en production)


def products_request():
    URL = "http://localhost:8000/products/get"  # Vérifie que le prefix n'est pas doublé

    params = {"title": "chaise", "brand": "TROttINE"}
    headers = {"x-api-key": API_KEY}

    r = requests.get(URL, headers=headers, params=params)
    print(json.dumps(r.json(), indent=2))


def products_by_ids_request():
    URL = "http://localhost:8000/products/get_by_ids"  # Vérifie que le prefix n'est pas doublé

    params = {"ids": [1, 2, 3, 4, 5, 4]}
    headers = {"x-api-key": API_KEY}

    r = requests.get(URL, headers=headers, params=params)
    print(json.dumps(r.json(), indent=2))


products_request()

print("\n--- Start of test_product_search.py ---")
products_by_ids_request()
print("\n--- End of test_product_search.py ---")
