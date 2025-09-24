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
        with open("api_products/assets/json/es_mapping.json", "r") as f:
            mapping = json.load(f)
        es.indices.create(index=ES_INDEX, body=mapping)
        print(f"✅ Index '{ES_INDEX}' created with mapping.")
        reindex_products()
    else:
        print(f"ℹ️ Index '{ES_INDEX}' already exists, skipping creation.")


def reindex_products():
    """Delete existing docs and load products from products.json into Elasticsearch."""
    try:
        with open("api_products/assets/json/products.json", "r") as f:
            products = json.load(f)

        # Delete all existing docs in the index
        es.delete_by_query(index=ES_INDEX, body={"query": {"match_all": {}}})

        actions = [
            {"_index": ES_INDEX, "_id": product["id"], "_source": product}
            for product in products
        ]
        helpers.bulk(es, actions)

        print(f"✅ {len(products)} products reindexed into '{ES_INDEX}'")
    except FileNotFoundError:
        print("⚠️ products.json file not found, no products indexed")


def __get_products(
    title: str = None, brand: str = None, category: str = None, fields: list = None
):
    """
    Search for products with flexible filtering logic
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


def __get_products_by_ids(ids: list):
    """
    Retrieve products by their product_ids.
    Returns results in the same order as requested (skips missing).
    """

    if not ids:
        return []

    # sanitize and deduplicate ids while preserving order
    seen = set()
    ordered_ids = []
    for i in ids:
        sid = str(i).strip()
        if sid and sid not in seen:
            seen.add(sid)
            ordered_ids.append(sid)

    # _source filtering
    mget_body = {"ids": ordered_ids}
    params = {}
    try:
        res = es.mget(index=ES_INDEX, body=mget_body, params=params)
        hits = {doc["_id"]: doc["_source"] for doc in res["docs"] if doc.get("found")}

        # preserve requested order
        return [hits[i] for i in ordered_ids if i in hits]

    except Exception as e:
        print(f"Error fetching products by ids: {e}")
        return []


def __get_product_categories():
    """
    Retrieve product categories from data_store.json
    """
    try:
        with open(
            "api_products/assets/json/data_store.json", "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
            categories = data.get("categories", [])
            return categories
    except Exception as e:
        print(f"Error fetching product categories: {e}")
        return []


create_index_if_missing()

# TODO: Dirty solution to reset the index during development to match changes in products.json. Implement a better strategy later to prevent Downtime.
reindex_products()

# We could also use delete index in developer mode using : `Invoke-RestMethod -Method Delete -Uri "http://localhost:9200/products"`
