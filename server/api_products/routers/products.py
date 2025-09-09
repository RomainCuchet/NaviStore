from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from api_products.crud import search_products
from api_products.auth import verify_api_key, require_write_rights

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/")
async def get_products(
    title: Optional[str] = Query(None, description="Text to search in product titles"),
    brand: Optional[str] = Query(None, description="Exact brand name to filter"),
    category: Optional[str] = Query(None, description="Exact category to filter"),
    fields: Optional[str] = Query(
        None, description="Fields to include, separated by commas"
    ),
    user_info: dict = Depends(verify_api_key),  # récupère user + role
):
    """
    Endpoint to search for products with flexible filtering.

    Search logic:
    - If title is provided: search by title + optional brand/category filters
    - If no title: at least brand OR category must be provided

    Accessible à tous (read et write).
    """
    brand = brand.lower() if brand else brand
    category = category.lower() if category else category

    # Validation : si pas de title, au moins brand ou category requis
    if not title and not brand and not category:
        raise HTTPException(
            status_code=422,
            detail="Si aucun 'title' n'est spécifié, au moins 'brand' ou 'category' doit être fourni",
        )

    # Conversion des fields en liste si fourni
    field_list = fields.split(",") if fields else None

    try:
        # Appel à la fonction search_products mise à jour
        results = search_products(
            title=title, brand=brand, category=category, fields=field_list
        )

        return {
            "requested_by": user_info["user"],
            "role": user_info["role"],
            "search_params": {
                "title": title,
                "brand": brand,
                "category": category,
                "fields": field_list,
            },
            "count": len(results),
            "results": results,
        }

    except ValueError as e:
        # Capture les erreurs de validation de la fonction search_products
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Capture toute autre erreur
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


# Endpoint de compatibilité pour l'ancienne API (optionnel)
@router.get("/legacy")
async def get_products_legacy(
    q: str = Query(..., description="Product's search query (legacy endpoint)"),
    fields: Optional[str] = Query(
        None, description="Fields to include, separated by commas"
    ),
    user_info: dict = Depends(verify_api_key),
):
    """
    Endpoint de compatibilité pour l'ancienne API utilisant le paramètre 'q'.
    Le paramètre 'q' est traité comme une recherche de titre.

    **DEPRECATED**: Utilisez l'endpoint principal avec les paramètres title/brand/category.
    """
    field_list = fields.split(",") if fields else None

    try:
        # Utilise q comme title dans la nouvelle fonction
        results = search_products(title=q, fields=field_list)

        return {
            "requested_by": user_info["user"],
            "role": user_info["role"],
            "legacy_query": q,
            "results": results,
            "warning": "Cet endpoint est déprécié. Utilisez /products/ avec les paramètres title/brand/category.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


# POST endpoint to add a product (protected, write only)
# @router.post("/")
# async def add_product(
#     product: dict,
#     user_info: dict = Depends(require_write_rights),  # protège l'accès
# ):
#     """
#     Endpoint to add a product.
#     Accessible uniquement aux utilisateurs avec role=write (ex: admin).
#     """
#     return {
#         "message": f"Produit ajouté par {user_info['user']} (role={user_info['role']})",
#         "product": product,
#     }


# Endpoint pour obtenir des informations sur les filtres disponibles
@router.get("/filters")
async def get_available_filters(
    user_info: dict = Depends(verify_api_key),
):
    """
    Endpoint pour récupérer les valeurs possibles pour les filtres brand et category.
    Utile pour construire des interfaces utilisateur dynamiques.
    """
    try:
        # Cette partie nécessiterait une fonction dans crud.py pour récupérer les valeurs uniques
        # Pour l'instant, on retourne un exemple
        return {
            "requested_by": user_info["user"],
            "role": user_info["role"],
            "message": "Pour implémenter cette fonctionnalité, ajoutez une fonction get_unique_values dans crud.py",
            "example_usage": {
                "brands": ["Carrefour", "Leclerc", "Auchan"],
                "categories": ["Fruits", "Légumes", "Produits laitiers"],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
