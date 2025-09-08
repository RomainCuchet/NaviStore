from fastapi import APIRouter, Depends, Query
from typing import Optional
from api_products.crud import search_products
from api_products.auth import verify_api_key

router = APIRouter(prefix="/products", tags=["Products"])


from fastapi import APIRouter, Depends, Query
from typing import Optional
from api_products.crud import search_products
from api_products.auth import verify_api_key, require_write_rights

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/")
async def get_products(
    q: str = Query(..., description="Product's search query"),
    fields: Optional[str] = Query(
        None, description="Fields to include, separated by commas"
    ),
    user_info: dict = Depends(verify_api_key),  # récupère user + role
):
    """
    Endpoint to search for products.
    Accessible à tous (read et write).
    """
    field_list = fields.split(",") if fields else None
    return {
        "requested_by": user_info["user"],
        "role": user_info["role"],
        "results": search_products(q, field_list),
    }


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
