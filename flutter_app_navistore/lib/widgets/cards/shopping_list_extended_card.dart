import 'package:flutter/material.dart';
import '../../models/product_model.dart';
import '../../models/shopping_list_model.dart';
import '../../repositories/shopping_list_repository.dart';
import 'product_list_card.dart';

class ShoppingListExtendedCard extends StatefulWidget {
  final ShoppingListModel shoppingList;
  final VoidCallback? onDelete;

  const ShoppingListExtendedCard({
    super.key,
    required this.shoppingList,
    this.onDelete,
  });

  @override
  State<ShoppingListExtendedCard> createState() =>
      _ShoppingListExtendedCardState();
}

class _ShoppingListExtendedCardState extends State<ShoppingListExtendedCard> {
  List<ProductModel> products = [];
  bool _isLoading = true;
  bool _showInOtherView = false;
  late TextEditingController _nameController;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.shoppingList.name);
    _loadProductsFromHive();
  }

  /// Charge uniquement les produits depuis Hive
  Future<void> _loadProductsFromHive() async {
    setState(() => _isLoading = true);
    try {
      final allProducts = await ProductModel.getAllFromHive();
      final productMap = {for (var p in allProducts) p.id: p};

      final listProducts = widget.shoppingList.productIds.map((id) {
        // Produit trouvé dans Hive
        return productMap[id] ??
            ProductModel(
              id: id,
              name: "Produit inconnu",
              price: 0,
              category: "Inconnu",
              isAvailable: false,
            );
      }).toList();

      setState(() => products = listProducts);

      // Supprime les produits orphelins (non utilisés dans aucune liste)
      final allLists = await ShoppingListModel.getAllFromHive();
      final usedIds = allLists.expand((l) => l.productIds).toSet();
      for (var p in allProducts) {
        if (!usedIds.contains(p.id)) {
          await p.deleteFromHive();
        }
      }
    } catch (e) {
      print("❌ Failed to load products from Hive: $e");
      setState(() => products = []);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  double get totalAvailable =>
      products.where((p) => p.isAvailable).fold(0, (sum, p) => sum + p.price);
  double get totalAll => products.fold(0, (sum, p) => sum + p.price);

  Future<void> _deleteProduct(ProductModel product) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Supprimer le produit ?"),
        content: Text("Voulez-vous vraiment supprimer '${product.name}' ?"),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(ctx).pop(false),
              child: const Text("Annuler")),
          TextButton(
              onPressed: () => Navigator.of(ctx).pop(true),
              child: const Text("Supprimer")),
        ],
      ),
    );

    if (confirmed == true) {
      setState(() => products.remove(product));

      // Met à jour la liste Hive
      final repo = ShoppingListRepository();
      await repo.updateShoppingList(
        widget.shoppingList.copyWith(
          productIds: products.map((p) => p.id).toList(),
        ),
      );

      // Supprime le produit de Hive s’il n’est plus utilisé dans aucune liste
      final allLists = await ShoppingListModel.getAllFromHive();
      final usedIds = allLists.expand((l) => l.productIds).toSet();
      if (!usedIds.contains(product.id)) {
        await product.deleteFromHive();
      }
    }
  }

  Future<void> _updateListName() async {
    final newName = _nameController.text.trim();
    if (newName.isEmpty || newName == widget.shoppingList.name) return;

    setState(() => widget.shoppingList.name = newName);

    final repo = ShoppingListRepository();
    await repo.updateShoppingList(
      widget.shoppingList.copyWith(
        name: newName,
        productIds: products.map((p) => p.id).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sortedProducts = List<ProductModel>.from(products)
      ..sort((a, b) {
        if (a.isAvailable && !b.isAvailable) return -1;
        if (!a.isAvailable && b.isAvailable) return 1;
        return 0;
      });

    return Scaffold(
      backgroundColor: Colors.black.withOpacity(0.5),
      body: Center(
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: Container(
            width: MediaQuery.of(context).size.width * 0.9,
            height: MediaQuery.of(context).size.height * 0.8,
            color: theme.colorScheme.surface,
            child: Stack(
              children: [
                // Liste des produits
                Padding(
                  padding: const EdgeInsets.only(top: 100, bottom: 60),
                  child: _isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : ListView.builder(
                          itemCount: sortedProducts.length,
                          itemBuilder: (context, index) {
                            final product = sortedProducts[index];
                            return ProductListCard(
                              product: product,
                              strikeFields: !product.isAvailable,
                              onDelete: () => _deleteProduct(product),
                            );
                          },
                        ),
                ),

                // Nom de la liste + switch
                Positioned(
                  top: 16,
                  left: 16,
                  right: 120,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _nameController,
                          style: theme.textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: theme.colorScheme.onSurface),
                          decoration: const InputDecoration(
                            border: InputBorder.none,
                          ),
                          onSubmitted: (_) => _updateListName(),
                        ),
                      ),
                      Row(
                        children: [
                          Text(
                            _showInOtherView ? "Revealed" : "Hidden",
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: _showInOtherView
                                  ? theme.colorScheme.primary
                                  : theme.colorScheme.onSurfaceVariant,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Switch.adaptive(
                            value: _showInOtherView,
                            activeColor: theme.colorScheme.primary,
                            onChanged: (val) =>
                                setState(() => _showInOtherView = val),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // Bouton fermer
                Positioned(
                  top: 16,
                  right: 16,
                  child: IconButton(
                    icon: Icon(Icons.close,
                        size: 28, color: theme.colorScheme.onSurface),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ),

                // Bouton supprimer la liste
                Positioned(
                  top: 16,
                  right: 60,
                  child: IconButton(
                    icon: Icon(Icons.delete_outline,
                        size: 28, color: theme.colorScheme.error),
                    onPressed: () async {
                      final confirmed = await showDialog<bool>(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: const Text("Supprimer la liste ?"),
                          content: Text(
                              "Voulez-vous vraiment supprimer la liste '${widget.shoppingList.name}' ?"),
                          actions: [
                            TextButton(
                                onPressed: () => Navigator.of(ctx).pop(false),
                                child: const Text("Annuler")),
                            TextButton(
                                onPressed: () => Navigator.of(ctx).pop(true),
                                child: const Text("Supprimer")),
                          ],
                        ),
                      );
                      if (confirmed == true && widget.onDelete != null) {
                        widget.onDelete!();
                        Navigator.of(context).pop();
                      }
                    },
                  ),
                ),

                // Footer
                Positioned(
                  bottom: 0,
                  left: 0,
                  right: 0,
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    color: theme.colorScheme.surfaceVariant,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          "Available ${products.where((p) => p.isAvailable).length}/${products.length}",
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                        Text(
                          "Price : ${totalAvailable.toStringAsFixed(2)} € / ${totalAll.toStringAsFixed(2)} €",
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
