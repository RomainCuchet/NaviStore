from fastapi import FastAPI
from api_products.routers import products, path_optimization

app = FastAPI(title="API Produits")

# Include routers
app.include_router(products.router)
app.include_router(path_optimization.router)
