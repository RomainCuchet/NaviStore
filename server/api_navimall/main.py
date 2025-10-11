from fastapi import FastAPI, logger
from api_navimall.routers import products, path_optimization, health
from contextlib import asynccontextmanager
import logging
import os


from api_navimall.crud import (
    create_index_if_missing,
    reindex_products,
    _upload_store_layout,
)
from api_navimall.utils import file_to_upload_file

logging.basicConfig(level=logging.INFO)
l = logging.getLogger(__name__)


async def init_layout():

    # Create directories for caching
    os.makedirs("assets/cache", exist_ok=True)
    os.makedirs("assets/layouts", exist_ok=True)

    # Ensure a default layout is uploaded for testing if none exists
    default_layout_hash_file = os.path.join("assets/cache", "default_layout.json")

    try:
        with open("default_layout.h5", "rb") as f:
            if not os.path.exists(default_layout_hash_file):
                upload_file = file_to_upload_file(f, "default_layout.h5")
                await _upload_store_layout(upload_file, {"user": "system_init"})

    except Exception as e:
        l.error(f"Error initializing default layout: {e}")

    create_index_if_missing()

    # TODO: Dirty solution to reset the index during development to match changes in products.json. Implement a better strategy later to prevent Downtime.
    reindex_products()
    # We could also use delete index in developer mode using : `Invoke-RestMethod -Method Delete -Uri "http://localhost:9200/products"`

    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    await init_layout()
    l.info("App started ✅")

    yield  # ⬅️ Ici, FastAPI exécute ton app pendant ce temps

    # --- shutdown ---
    # await close_connections()
    print("App stopped 🛑")


app = FastAPI(title="API Produits", lifespan=lifespan)

# Include routers
app.include_router(products.router)
app.include_router(path_optimization.router)
app.include_router(health.router)
