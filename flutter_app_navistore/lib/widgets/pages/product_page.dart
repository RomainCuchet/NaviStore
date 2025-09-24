import 'package:flutter/material.dart';
import '../../models/product_model.dart';
import '../../services/product_api_service.dart';
import '../../repositories/shopping_list_repository.dart';
import '../../models/shopping_list_model.dart';

class ProductsPage extends StatefulWidget {
  final ProductApiService api;

  const ProductsPage({super.key, required this.api});

  @override
  State<ProductsPage> createState() => _ProductsPageState();
}

class _ProductsPageState extends State<ProductsPage> {
  List<ProductModel> products = [];
  String searchQuery = "";
  String? selectedBrand;
  String? selectedCategory;

  List<String> availableCategories = [];
  bool isLoadingCategories = true;

  bool isLoading = false;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    setState(() => isLoadingCategories = true);
    try {
      final categories = await widget.api.fetchCategories();
      setState(() => availableCategories = categories);
    } catch (e) {
      print("❌ Failed to load categories: $e");
      setState(() => availableCategories = []);
    } finally {
      setState(() => isLoadingCategories = false);
    }
  }

  Future<void> loadProducts() async {
    if (searchQuery.isEmpty &&
        selectedBrand == null &&
        selectedCategory == null) {
      setState(() {
        products = [];
        errorMessage = null;
      });
      return;
    }

    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final fetched = await widget.api.getProducts(
        title: searchQuery.isNotEmpty ? searchQuery : null,
        brand: selectedBrand,
        category: selectedCategory,
      );
      setState(() {
        products = fetched;
        if (products.isEmpty) errorMessage = "Aucun produit trouvé";
      });
    } catch (e) {
      setState(() {
        products = [];
        errorMessage = "Erreur lors de la récupération des produits";
      });
      print("❌ API error: $e");
    } finally {
      setState(() => isLoading = false);
    }
  }

  void _onProductTap(ProductModel product) async {
    final repo = ShoppingListRepository();
    final lists = await repo.getAllLists();

    showModalBottomSheet(
      context: context,
      builder: (ctx) => ListView(
        shrinkWrap: true,
        children: [
          const ListTile(title: Text("Ajouter à une liste existante")),
          ...lists.map((list) => ListTile(
                title: Text(list.name),
                onTap: () async {
                  await repo.addProductToList(list.id, product);
                  Navigator.pop(ctx);
                },
              )),
          const Divider(),
          ListTile(
            title: const Text("Créer une nouvelle liste"),
            onTap: () async {
              final newList = ShoppingListModel(
                id: DateTime.now().millisecondsSinceEpoch.toString(),
                name: "Nouvelle liste",
                productIds: [product.id],
              );
              await repo.addShoppingList(newList);
              await product.saveToHive();
              Navigator.pop(ctx);
            },
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Produits"),
        centerTitle: true,
      ),
      body: Column(
        children: [
          // Barre de recherche
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              decoration: InputDecoration(
                hintText: "Rechercher un produit...",
                prefixIcon: const Icon(Icons.search),
                suffixIcon: searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          setState(() {
                            searchQuery = "";
                            products = [];
                            errorMessage = null;
                          });
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onChanged: (val) => searchQuery = val.trim(),
              onSubmitted: (_) => loadProducts(),
              textInputAction: TextInputAction.search,
            ),
          ),

          // Filtres Row
          Row(
            children: [
              DropdownButton<String>(
                hint: const Text("Category filter"),
                value: selectedCategory,
                items: isLoadingCategories
                    ? [
                        const DropdownMenuItem(
                            value: null, child: Text("Chargement..."))
                      ]
                    : availableCategories.map((brand) {
                        return DropdownMenuItem(
                            value: brand, child: Text(brand));
                      }).toList(),
                onChanged: (val) {
                  setState(() => selectedCategory = val);
                },
              ),
            ],
          ),

          const SizedBox(height: 8),

          Expanded(
            child: isLoading
                ? const Center(child: CircularProgressIndicator())
                : errorMessage != null
                    ? Center(
                        child: Text(
                          errorMessage!,
                          style: const TextStyle(fontSize: 16),
                        ),
                      )
                    : ListView.builder(
                        itemCount: products.length,
                        itemBuilder: (_, index) {
                          final product = products[index];
                          return Card(
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16)),
                            margin: const EdgeInsets.all(8),
                            child: ListTile(
                              leading: Image.network(
                                product.imagePath,
                                width: 50,
                                height: 50,
                                fit: BoxFit.cover,
                              ),
                              title: Text(product.name),
                              subtitle:
                                  Text("${product.brand} • ${product.price} €"),
                              onTap: () => _onProductTap(product),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
