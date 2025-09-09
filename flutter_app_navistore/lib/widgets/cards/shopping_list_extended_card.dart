import 'package:flutter/material.dart';
import 'product_card.dart';
import '../../models/product.dart';

class ShoppingListExtendedCard extends StatelessWidget {
  final String listName;
  final List<Product> products;

  const ShoppingListExtendedCard({
    super.key,
    required this.listName,
    required this.products,
  });

  double get totalAvailable =>
      products.where((p) => p.isAvailable).fold(0, (sum, p) => sum + p.price);

  double get totalAll => products.fold(0, (sum, p) => sum + p.price);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // 🔹 Trier les produits : disponibles d'abord, non disponibles à la fin
    final sortedProducts = List<Product>.from(products)
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
                // ListView des produits
                Padding(
                  padding: const EdgeInsets.only(top: 80, bottom: 60),
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
                // Nom de la liste
                Positioned(
                  top: 16,
                  left: 16,
                  child: Text(
                    listName,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                ),
                // Bouton de fermeture
                Positioned(
                  top: 16,
                  right: 16,
                  child: IconButton(
                    icon: Icon(Icons.close,
                        size: 28, color: theme.colorScheme.onSurface),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ),
                // Prix total
                // Footer avec disponibilité et total
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
                        // À gauche : Available x/n
                        Text(
                          "Available ${products.where((p) => p.isAvailable).length}/${products.length}",
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                        // À droite : Total : disponible / total
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
