## Elastic Search
Elastic Search is a powerful distributed search engine that perfectly suits our project's needs for several reasons:

1. **Full-Text Search Optimization**: We leverage Elastic Search for efficient full-text search across product titles, providing fast and relevant results.

2. **Document-Based Storage**: Products are indexed using their IDs as document identifiers (_id), enabling optimized multi-get (mget) operations for quick retrievals.

3. **Advanced Filtering**: The engine supports complex search parameters as filters without significant performance impact, allowing refined search results.

4. **Scalability**: Built for distributed systems, it can handle growing product catalogs efficiently.

## Implementation Notes
- To delete index in developer mode: `Invoke-RestMethod -Method Delete -Uri "http://localhost:9200/products"`