import 'package:flutter/material.dart';

import '../../models/product_model.dart';
import '../../models/shopping_list_model.dart';
import '../../models/product_categories_model.dart';

import '../../services/product_api_service.dart';

import '../../repositories/shopping_list_repository.dart';

import '../cards/product_detail_card_browse.dart';
import '../cards/product_list_card_browse.dart';

class BrowseProductsPage extends StatefulWidget {
  final ProductApiService productService;

  const BrowseProductsPage({super.key, required this.productService});

  @override
  State<BrowseProductsPage> createState() => _BrowseProductsPageState();
}

class _BrowseProductsPageState extends State<BrowseProductsPage> {
  List<ProductModel> allResults = [];
  List<ProductModel> filteredResults = [];
  String searchQuery = "";
  String? selectedCategory;

  ProductCategoriesModel categories =
      ProductCategoriesModel(productCategories: []);

  bool isLoadingCategories = true;

  bool isLoading = false;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    ProductCategoriesModel.getFromHive().then((categories) {
      setState(() {
        this.categories = categories;
      }); // si tu veux rafraîchir l’UI
    }).catchError((err) {
      print("Erreur : $err");
    });
  }

  Future<void> loadProducts() async {
    if (searchQuery.isEmpty) {
      setState(() {
        allResults = [];
        filteredResults = [];
        errorMessage = null;
      });
      return;
    }

    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final fetched =
          await widget.productService.getProducts(title: searchQuery);
      setState(() {
        allResults = fetched;
        _applyFilters();
        if (filteredResults.isEmpty) errorMessage = "Aucun produit trouvé";
      });
    } catch (e) {
      setState(() {
        allResults = [];
        filteredResults = [];
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
      filteredResults = filtered;
      errorMessage = filteredResults.isEmpty ? "Aucun produit trouvé" : null;
    });
  }

  Future<void> _onProductTap(ProductModel product) async {
    final repo = ShoppingListsRepository();
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
                showInOtherView: false,
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
        title: const Text("Products Browser"),
        centerTitle: true,
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              decoration: InputDecoration(
                hintText: "Search for a product...",
                prefixIcon: const Icon(Icons.search),
                suffixIcon: searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          setState(() {
                            searchQuery = "";
                            allResults = [];
                            filteredResults = [];
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

          // Filter by category
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Filter by category:",
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Autocomplete<String>(
                  optionsBuilder: (textEditingValue) {
                    if (textEditingValue.text.isEmpty)
                      return categories.productCategories;
                    return categories.productCategories.where((cat) => cat
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
                        hintText: "Select or type a category",
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

          // Chip filter active
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

          // Products list
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
                        itemCount: filteredResults.length,
                        itemBuilder: (_, index) {
                          final product = filteredResults[index];
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
