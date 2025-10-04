import json
import os
import requests
from urllib.parse import urlparse, parse_qs

# Chemins
JSON_FILE = "../api_products/assets/json/products.json"
IMAGES_DIR = os.path.join("..", "assets", "products_images")

os.makedirs(IMAGES_DIR, exist_ok=True)

# Charge le JSON
with open(JSON_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

for product in products:
    image_url = product.get("image_url")
    if not image_url:
        continue

    # Extraire le nom du fichier après 'media/'
    parsed_url = urlparse(image_url)
    path_parts = parsed_url.path.split("/")
    if "media" in path_parts:
        media_index = path_parts.index("media")
        filename = path_parts[media_index + 1]
    else:
        # fallback si pas de 'media'
        filename = os.path.basename(parsed_url.path)

    # Ajouter l'extension si nécessaire
    if not os.path.splitext(filename)[1]:
        filename += ".jpg"

    save_path = os.path.join(IMAGES_DIR, filename)

    # Télécharger l'image
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        with open(save_path, "wb") as img_file:
            img_file.write(response.content)
        print(f"✅ {filename} téléchargé.")
    except Exception as e:
        print(f"❌ Erreur pour {filename}: {e}")
