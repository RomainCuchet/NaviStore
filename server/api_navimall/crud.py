# crud stands for Create, Read, Update, Delete

import json
import time
import logging
from typing import Optional
from elasticsearch import Elasticsearch, helpers, ConnectionError, ConnectionTimeout
from api_navimall.config import ES_HOST, ES_INDEX

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_elasticsearch(
    host: str = ES_HOST,
    max_wait_time: int = 300,  # 5 minutes max
    initial_wait: float = 1.0,  # Commencer par 1 seconde
    max_interval: float = 30.0,  # Intervalle max de 30 secondes
    backoff_factor: float = 1.5,  # Facteur d'augmentation
) -> Elasticsearch:
    """
    Attend qu'Elasticsearch soit prêt avec une stratégie de retry optimisée.

    Args:
        host: Host Elasticsearch
        max_wait_time: Temps d'attente maximum en secondes
        initial_wait: Délai initial entre les tentatives
        max_interval: Délai maximum entre les tentatives
        backoff_factor: Facteur d'augmentation du délai

    Returns:
        Instance Elasticsearch connectée

    Raises:
        ConnectionError: Si Elasticsearch n'est pas disponible après max_wait_time
    """
    start_time = time.time()
    wait_interval = initial_wait
    attempt = 1

    logger.info(f"🔍 Attente d'Elasticsearch sur {host}...")

    while time.time() - start_time < max_wait_time:
        try:
            # Créer le client Elasticsearch avec la bonne configuration
            es = Elasticsearch(
                hosts=[host], request_timeout=5, max_retries=1, retry_on_timeout=True
            )

            # Test de ping simple
            if es.ping():
                logger.info(f"🏥 Ping OK - Vérification de la santé du cluster...")

                # Vérification de la santé du cluster
                try:
                    health = es.cluster.health(timeout="10s")
                    status = health.get("status", "unknown")

                    if status in ["green", "yellow"]:
                        elapsed = time.time() - start_time
                        logger.info(
                            f"✅ Elasticsearch prêt ! (statut: {status}, "
                            f"temps d'attente: {elapsed:.1f}s, tentatives: {attempt})"
                        )
                        return es
                    else:
                        logger.warning(f"⚠️ Cluster en statut '{status}', attente...")

                except Exception as health_error:
                    logger.warning(f"⚠️ Erreur santé cluster: {health_error}")

            else:
                logger.debug(f"🔍 Ping échoué (tentative {attempt})")

        except (ConnectionError, ConnectionTimeout) as e:
            logger.debug(
                f"🔍 Connexion échouée (tentative {attempt}): {type(e).__name__}"
            )
        except Exception as e:
            logger.warning(f"⚠️ Erreur inattendue (tentative {attempt}): {e}")

        # Attendre avant la prochaine tentative
        elapsed = time.time() - start_time
        remaining = max_wait_time - elapsed

        if remaining <= wait_interval:
            logger.error(
                f"❌ Timeout atteint ({max_wait_time}s) - Elasticsearch non disponible"
            )
            raise ConnectionError(
                f"Elasticsearch non disponible après {max_wait_time}s d'attente"
            )

        logger.info(
            f"⏳ Tentative {attempt} échouée, nouvelle tentative dans {wait_interval:.1f}s "
            f"(temps écoulé: {elapsed:.1f}s/{max_wait_time}s)"
        )

        time.sleep(wait_interval)

        # Augmenter l'intervalle avec backoff exponentiel
        wait_interval = min(wait_interval * backoff_factor, max_interval)
        attempt += 1

    raise ConnectionError(f"Elasticsearch non disponible après {max_wait_time}s")


# Initialisation avec attente optimisée
logger.info("🚀 Initialisation de la connexion Elasticsearch...")
es = wait_for_elasticsearch()


def get_elasticsearch_health() -> dict:
    """
    Récupère l'état de santé d'Elasticsearch.

    Returns:
        Dictionnaire avec les informations de santé
    """
    try:
        if not es.ping():
            return {"status": "unreachable", "error": "Ping failed"}

        health = es.cluster.health(timeout="5s")

        return {
            "status": health.get("status", "unknown"),
            "cluster_name": health.get("cluster_name", "unknown"),
            "number_of_nodes": health.get("number_of_nodes", 0),
            "active_primary_shards": health.get("active_primary_shards", 0),
            "active_shards": health.get("active_shards", 0),
            "relocating_shards": health.get("relocating_shards", 0),
            "initializing_shards": health.get("initializing_shards", 0),
            "unassigned_shards": health.get("unassigned_shards", 0),
            "delayed_unassigned_shards": health.get("delayed_unassigned_shards", 0),
            "pending_tasks": health.get("number_of_pending_tasks", 0),
            "in_flight_fetch": health.get("number_of_in_flight_fetch", 0),
            "task_max_waiting_in_queue_millis": health.get(
                "task_max_waiting_in_queue_millis", 0
            ),
            "active_shards_percent_as_number": health.get(
                "active_shards_percent_as_number", 0.0
            ),
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


def ensure_elasticsearch_connection() -> bool:
    """
    S'assure que la connexion Elasticsearch est active.
    Reconnecte si nécessaire.

    Returns:
        True si la connexion est active, False sinon
    """
    global es

    try:
        if es.ping():
            return True

        logger.warning("🔄 Connexion Elasticsearch perdue, tentative de reconnexion...")
        es = wait_for_elasticsearch(
            max_wait_time=60
        )  # Attente réduite pour reconnexion
        return True

    except Exception as e:
        logger.error(f"❌ Impossible de rétablir la connexion Elasticsearch: {e}")
        return False


def create_index_if_missing():
    """Create the index with mapping if it doesn't exist."""
    if not es.indices.exists(index=ES_INDEX).body:
        with open("api_navimall/assets/json/es_mapping.json", "r") as f:
            mapping = json.load(f)
        es.indices.create(index=ES_INDEX, body=mapping)
        print(f"✅ Index '{ES_INDEX}' created with mapping.")
        reindex_products()
    else:
        print(f"ℹ️ Index '{ES_INDEX}' already exists, skipping creation.")


def reindex_products():
    """Delete existing docs and load products from products.json into Elasticsearch."""
    try:
        with open("api_navimall/assets/json/products.json", "r") as f:
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
            "api_navimall/assets/json/data_store.json", "r", encoding="utf-8"
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
