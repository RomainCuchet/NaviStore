## Tips
- In elasticsearch developer mode use `Invoke-RestMethod -Method Delete -Uri "http://localhost:9200/products"` to delete index
- For a reason I didn't pinpoint product and category must be lowercase for the search to work, evethough it's uppercase in the products.json 