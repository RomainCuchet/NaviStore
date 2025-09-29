import 'package:flutter/material.dart';
import '../../models/product_model.dart';
import '../../services/product_api_service.dart';
import '../../repositories/shopping_list_repository.dart';
import '../../models/shopping_list_model.dart';
import '../cards/product_detail_card_browse.dart';
import '../cards/product_list_card_browse.dart';

class BrowseProductsPage extends StatefulWidget {
  final ProductApiService api;

  const BrowseProductsPage({super.key, required this.api});

  @override
  State<BrowseProductsPage> createState() => _BrowseProductsPageState();
}

class _BrowseProductsPageState extends State<BrowseProductsPage> {
  List<ProductModel> allResults = []; // bruts de l’API
  List<ProductModel> products = []; // affichés après filtres
  String searchQuery = "";
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
      categories.sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));
      setState(() => availableCategories = categories);
    } catch (e) {
      print("❌ Failed to load categories: $e");
      setState(() => availableCategories = []);
    } finally {
      setState(() => isLoadingCategories = false);
    }
  }

  Future<void> loadProducts() async {
    if (searchQuery.isEmpty) {
      setState(() {
        allResults = [];
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
      final fetched = await widget.api.getProducts(title: searchQuery);
      setState(() {
        allResults = fetched;
        _applyFilters();
        if (products.isEmpty) errorMessage = "Aucun produit trouvé";
      });
    } catch (e) {
      setState(() {
        allResults = [];
        products = [];
        errorMessage = "Erreur lors de la récupération des produits";
      });
      print("❌ API error: $e");
    } finally {
      setState(() => isLoading = false);
    }
  }

  void _applyFilters() {
    List<ProductModel> filtered = List.from(allResults);

    if (selectedCategory != null) {
      filtered = filtered
          .where((p) =>
              p.category.toLowerCase() == selectedCategory!.toLowerCase())
          .toList();
    }

    setState(() {
      products = filtered;
      errorMessage = products.isEmpty ? "Aucun produit trouvé" : null;
    });
  }

  Future<void> _onProductTap(ProductModel product) async {
    final repo = ShoppingListRepository();
    final lists = await repo.getAllShoppingLists();

    showModalBottomSheet(
      context: context,
      builder: (ctx) => ListView(
        shrinkWrap: true,
        children: [
          const ListTile(title: Text("Ajouter à une liste existante")),
          ...lists.map((list) => ListTile(
                title: Text(list.name),
                onTap: () async {
                  // Sauvegarde le produit dans Hive (box "products")
                  await product.saveToHive();

                  // Ajoute uniquement son ID à la liste
                  await repo.addProductToList(list.id, product.id.toString());

                  Navigator.pop(ctx);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                        content: Text("${product.name} ajouté à ${list.name}")),
                  );
                },
              )),
          const Divider(),
          ListTile(
            title: const Text("Créer une nouvelle liste"),
            onTap: () async {
              // Sauvegarde du produit dans Hive
              await product.saveToHive();

              // Crée une nouvelle liste avec uniquement son ID
              final newList = ShoppingListModel(
                id: DateTime.now().millisecondsSinceEpoch.toString(),
                name: "Nouvelle liste",
                productIds: [product.id.toString()],
              );
              await repo.addShoppingList(newList);

              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                    content: Text("${product.name} ajouté à ${newList.name}")),
              );
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
                            allResults = [];
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

          // Filtre catégorie
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Filtrer par catégorie",
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Autocomplete<String>(
                  optionsBuilder: (textEditingValue) {
                    if (textEditingValue.text.isEmpty)
                      return availableCategories;
                    return availableCategories.where((cat) => cat
                        .toLowerCase()
                        .contains(textEditingValue.text.toLowerCase()));
                  },
                  onSelected: (val) {
                    setState(() => selectedCategory = val);
                    _applyFilters();
                  },
                  fieldViewBuilder:
                      (context, controller, focusNode, onEditingComplete) {
                    controller.text = selectedCategory ?? '';
                    return TextField(
                      controller: controller,
                      focusNode: focusNode,
                      onEditingComplete: onEditingComplete,
                      decoration: InputDecoration(
                        hintText: "Sélectionner ou taper une catégorie",
                        suffixIcon: selectedCategory != null
                            ? IconButton(
                                icon: const Icon(Icons.clear),
                                onPressed: () {
                                  setState(() => selectedCategory = null);
                                  controller.clear();
                                  _applyFilters();
                                },
                              )
                            : null,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),

          // Chip filtre actif
          if (selectedCategory != null)
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Wrap(
                spacing: 8,
                children: [
                  InputChip(
                    label: Text(selectedCategory!),
                    onDeleted: () {
                      setState(() => selectedCategory = null);
                      _applyFilters();
                    },
                  ),
                ],
              ),
            ),

          const SizedBox(height: 8),

          // Liste produits
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
                          return ProductListCardBrowse(
                            product: product,
                            onTap: () {
                              showDialog(
                                context: context,
                                builder: (ctx) => ProductDetailCardBrowse(
                                  product: product,
                                  onAddToList: () => _onProductTap(product),
                                ),
                              );
                            },
                            onAddToList: () => _onProductTap(product),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
