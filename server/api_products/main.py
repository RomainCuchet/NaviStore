from fastapi import FastAPI
from api_products.routers import products

app = FastAPI(title="API Produits")

# save the products router
app.include_router(products.router)
