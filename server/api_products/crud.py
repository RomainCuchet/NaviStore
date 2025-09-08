# crud stands for Create, Read, Update, Delete

import json
import time
from elasticsearch import Elasticsearch, helpers
from api_products.config import ES_HOST, ES_INDEX

max_retries = 10
wait_time = 5

# TODO: replace with a proper healthcheck instead of a fixed sleep
time.sleep(240)  #

# Try connecting to Elasticsearch with retries
for attempt in range(max_retries):
    try:
        es = Elasticsearch(ES_HOST)
        if es.ping():
            print("✅ Elasticsearch is available")
            break
    except Exception:
        if attempt < max_retries - 1:
            print(
                f"⏳ Attempt {attempt+1}/{max_retries} failed, retrying in {wait_time}s"
            )
            time.sleep(wait_time)
        else:
            raise


def create_index_if_missing():
    """Create the index with mapping if it doesn't exist."""
    if not es.indices.exists(index=ES_INDEX).body:
        with open("api_products/es_mapping.json", "r") as f:
            mapping = json.load(f)
        es.indices.create(index=ES_INDEX, body=mapping)
        print(f"✅ Index '{ES_INDEX}' created with mapping.")
        reindex_products()
    else:
        print(f"ℹ️ Index '{ES_INDEX}' already exists, skipping creation.")


def reindex_products():
    """Delete existing docs and load products from products.json into Elasticsearch."""
    try:
        with open("api_products/products.json", "r") as f:
            products = json.load(f)

        # Delete all existing docs in the index
        es.delete_by_query(index=ES_INDEX, body={"query": {"match_all": {}}})

        actions = [{"_index": ES_INDEX, "_source": product} for product in products]

        helpers.bulk(es, actions)
        print(f"✅ {len(products)} products reindexed into '{ES_INDEX}'")
    except FileNotFoundError:
        print("⚠️ products.json file not found, no products indexed")


def search_products(
    title: str = None, brand: str = None, category: str = None, fields: list = None
):
    """
    Search for products with flexible filtering logic - VERSION CORRIGÉE pour mapping keyword
    """

    # Validation
    if not title and not brand and not category:
        raise ValueError(
            "Si aucun title n'est spécifié, au moins brand ou category doit être fourni"
        )

    # Construction de la requête
    query_body = {"query": {"bool": {}}}

    # Cas 1: Recherche par title avec filtres optionnels
    if title:
        query_body["query"]["bool"]["must"] = [
            {"match": {"title": {"query": title, "analyzer": "french"}}}
        ]

        # Ajout des filtres exacts si spécifiés
        filters = []
        if brand:
            filters.append({"term": {"brand": brand}})
        if category:
            filters.append({"term": {"category": category}})

        if filters:
            query_body["query"]["bool"]["filter"] = filters

    # Cas 2: Pas de title, filtrer uniquement par brand et/ou category
    else:
        filters = []
        if brand:
            # CORRECTION: brand est keyword, donc pas de .keyword
            filters.append({"term": {"brand": brand}})
        if category:
            filters.append({"term": {"category": category}})

        query_body["query"]["bool"]["filter"] = filters
        query_body["query"]["bool"]["must"] = [{"match_all": {}}]

    # Exécution de la requête
    try:
        res = es.search(index=ES_INDEX, body=query_body)
        hits = [hit["_source"] for hit in res["hits"]["hits"]]

        # Filtrage des champs si spécifié
        if fields:
            hits = [{k: v for k, v in hit.items() if k in fields} for hit in hits]

        return hits

    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")
        return []


# Ensure index exists at startup
create_index_if_missing()
