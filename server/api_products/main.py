from fastapi import FastAPI
from api_products.routers import products, path_optimization, health

app = FastAPI(title="API Produits")

# Include routers
app.include_router(products.router)
app.include_router(path_optimization.router)
app.include_router(health.router)
