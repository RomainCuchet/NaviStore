import 'package:flutter/material.dart';
import '../../models/product_model.dart';
import '../../models/shopping_list_model.dart';
import '../../repositories/shopping_list_repository.dart';
import 'product_list_card.dart';

class ShoppingListExtendedCard extends StatefulWidget {
  final ShoppingListModel shoppingList;
  final VoidCallback? onDelete; // callback pour suppression de la liste

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
  late List<ProductModel> products;
  bool _showInOtherView = false;

  @override
  void initState() {
    super.initState();
    // Clonage pour modification locale
    products = List<ProductModel>.from(widget.shoppingList.products);
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
            child: const Text("Annuler"),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text("Supprimer"),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      setState(() => products.remove(product));

      // Mise à jour Hive
      final repo = ShoppingListRepository();
      final updatedList = ShoppingListModel(
        id: widget.shoppingList.id,
        name: widget.shoppingList.name,
        products: List<ProductModel>.from(products),
      );
      await repo.updateShoppingList(updatedList);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // Tri : disponibles en haut
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
                  child: ListView.builder(
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
                  right: 70,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        widget.shoppingList.name,
                        style: theme.textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: theme.colorScheme.onSurface,
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
                            onChanged: (val) {
                              setState(() => _showInOtherView = val);
                            },
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
                              child: const Text("Annuler"),
                            ),
                            TextButton(
                              onPressed: () => Navigator.of(ctx).pop(true),
                              child: const Text("Supprimer"),
                            ),
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
              ],
            ),
          ),
        ),
      ),
    );
  }
}
