import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration Elasticsearch
ES_HOST = os.getenv("ES_HOST", "http://es:9200")
ES_INDEX = os.getenv("ES_INDEX", "products")

api_keys_raw = os.getenv("API_KEYS")

try:
    API_KEYS = json.loads(api_keys_raw) if api_keys_raw else {}
except json.JSONDecodeError:
    raise ValueError("The API_KEYS variable in .env must be a valid JSON")
