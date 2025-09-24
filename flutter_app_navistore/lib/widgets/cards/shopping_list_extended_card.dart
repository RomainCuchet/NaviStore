import 'package:flutter/material.dart';
import 'product_card.dart';
import '../../models/product_model.dart';

class ShoppingListExtendedCard extends StatefulWidget {
  final String listName;
  final List<ProductModel> products;

  const ShoppingListExtendedCard({
    super.key,
    required this.listName,
    required this.products,
  });

  @override
  State<ShoppingListExtendedCard> createState() =>
      _ShoppingListExtendedCardState();
}

class _ShoppingListExtendedCardState extends State<ShoppingListExtendedCard> {
  bool _showInOtherView = false; // état du toggle

  double get totalAvailable => widget.products
      .where((p) => p.isAvailable)
      .fold(0, (sum, p) => sum + p.price);

  double get totalAll => widget.products.fold(0, (sum, p) => sum + p.price);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final sortedProducts = List<ProductModel>.from(widget.products)
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
                      return ProductCard(
                        product: product,
                        strikeFields: !product.isAvailable,
                      );
                    },
                  ),
                ),

                // 🔹 Nom de la liste + switch toggle
                Positioned(
                  top: 16,
                  left: 16,
                  right: 70,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        widget.listName,
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
                          Padding(padding: const EdgeInsets.only(right: 8)),
                          Switch.adaptive(
                            value: _showInOtherView,
                            activeColor: theme.colorScheme.primary,
                            onChanged: (val) {
                              setState(() => _showInOtherView = val);
                              print(
                                "Toggle list '${widget.listName}' -> $val",
                              );
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
                          "Available ${widget.products.where((p) => p.isAvailable).length}/${widget.products.length}",
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
