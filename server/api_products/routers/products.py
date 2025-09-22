from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
import logging
import os

from api_products.crud import __get_products, __get_products_by_ids
from api_products.auth import verify_api_key, require_write_rights

router = APIRouter(prefix="/products", tags=["Products"])

os.makedirs("assets/log", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("assets/log/api_products.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("api_products")


@router.get("/get")
async def get_products(
    title: Optional[str] = Query(None, description="Text to search in product titles"),
    brand: Optional[str] = Query(None, description="Exact brand name to filter"),
    category: Optional[str] = Query(None, description="Exact category to filter"),
    user_info: dict = Depends(verify_api_key),  # récupère user + role
):
    """
    Endpoint to search for products with flexible filtering.

    Search logic:
    - If title is provided: search by title + optional brand/category filters
    - If no title: at least brand OR category must be provided

    """
    brand = brand.upper() if brand else brand
    # Category is case sensitive, so we don't modify it

    # Validation: if no title, at least brand or category is required
    if not title and not brand and not category:
        raise HTTPException(
            status_code=422,
            detail="If no 'title' is specified, at least 'brand' or 'category' must be provided",
        )

    try:
        results = __get_products(title=title, brand=brand, category=category)

        logger.info(
            "GET /products/get called by user=%s role=%s | title=%s brand=%s category=%s | results=%d",
            user_info["user"],
            user_info["role"],
            title,
            brand,
            category,
            len(results),
        )

        return {
            "count": len(results),
            "results": results,
        }

    except ValueError as e:
        # Capture validation errors from the search_products function
        logger.warning("Validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Internal error: %s", e)
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/get_by_ids")
async def get_products_by_ids(
    ids: list[int] = Query(None, description="List of product IDs to retrieve"),
    user_info: dict = Depends(verify_api_key),
):
    try:
        results = __get_products_by_ids(ids=ids)

        logger.info(
            "GET /products/get_by_ids called by user=%s role=%s | ids=%s | results=%d",
            user_info["user"],
            user_info["role"],
            ids,
            len(results),
        )

        return {
            "count": len(results),
            "results": results,
        }

    except ValueError as e:
        # Capture validation errors from the search_products function
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
