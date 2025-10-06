"""
Router pour la santé du système et diagnostics.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
from api_navimall.crud import get_elasticsearch_health, ensure_elasticsearch_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/elasticsearch")
async def elasticsearch_health() -> Dict[str, Any]:
    """
    Récupère l'état de santé d'Elasticsearch.

    Returns:
        État de santé détaillé d'Elasticsearch
    """
    health_info = get_elasticsearch_health()

    # Déterminer le code de statut HTTP basé sur l'état
    status = health_info.get("status", "unknown")

    if status == "green":
        http_status = 200
    elif status == "yellow":
        http_status = 200  # Acceptable mais avec avertissement
    elif status == "unreachable":
        http_status = 503  # Service Unavailable
    else:
        http_status = 500  # Internal Server Error

    if http_status != 200:
        raise HTTPException(status_code=http_status, detail=health_info)

    return {"status": "healthy", "elasticsearch": health_info, "timestamp": time.time()}


@router.get("/elasticsearch/reconnect")
async def elasticsearch_reconnect() -> Dict[str, Any]:
    """
    Force une reconnexion à Elasticsearch.

    Returns:
        Résultat de la reconnexion
    """
    start_time = time.time()

    try:
        success = ensure_elasticsearch_connection()
        elapsed_time = time.time() - start_time

        if success:
            health_info = get_elasticsearch_health()
            return {
                "status": "success",
                "message": "Reconnexion réussie",
                "elapsed_time": round(elapsed_time, 2),
                "elasticsearch": health_info,
                "timestamp": time.time(),
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "failed",
                    "message": "Impossible de se reconnecter à Elasticsearch",
                    "elapsed_time": round(elapsed_time, 2),
                    "timestamp": time.time(),
                },
            )

    except Exception as e:
        elapsed_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Erreur lors de la reconnexion: {str(e)}",
                "elapsed_time": round(elapsed_time, 2),
                "timestamp": time.time(),
            },
        )


@router.get("/")
async def system_health() -> Dict[str, Any]:
    """
    État de santé global du système.

    Returns:
        État de santé de tous les composants
    """
    elasticsearch_health = get_elasticsearch_health()

    # Évaluer la santé globale
    es_status = elasticsearch_health.get("status", "unknown")

    if es_status == "green":
        overall_status = "healthy"
    elif es_status == "yellow":
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "components": {
            "elasticsearch": elasticsearch_health,
            "api": {"status": "healthy"},  # L'API fonctionne si on peut répondre
        },
        "timestamp": time.time(),
    }
