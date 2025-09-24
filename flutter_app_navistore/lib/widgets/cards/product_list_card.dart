import 'package:flutter/material.dart';
import '../../models/product_model.dart';

class ProductListCard extends StatelessWidget {
  final ProductModel product;
  final bool strikeFields;

  const ProductListCard({
    super.key,
    required this.product,
    this.strikeFields = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    TextStyle? strikeStyle(TextStyle? style) {
      if (strikeFields) {
        return style?.copyWith(
          decoration: TextDecoration.lineThrough,
          color: theme.colorScheme.onSurfaceVariant,
        );
      }
      return style;
    }

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      clipBehavior: Clip.antiAlias,
      child: SizedBox(
        height: 120,
        child: Stack(
          children: [
            Row(
              children: [
                // 🔹 Image depuis le web avec fallback
                Container(
                  width: 120,
                  color: theme.colorScheme.surfaceVariant,
                  child: Image.network(
                    product.imagePath,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                      // image par défaut si le lien ne charge pas
                      return Image.asset(
                        'assets/icons/default_product_icon.png',
                        fit: BoxFit.cover,
                      );
                    },
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          product.name,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.onSurface,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(product.brand,
                            style: strikeStyle(theme.textTheme.bodyMedium)),
                        const SizedBox(height: 2),
                        Text(product.category,
                            style: strikeStyle(theme.textTheme.bodySmall)),
                        const Spacer(),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "${product.price.toStringAsFixed(2)} €",
                              style: strikeStyle(
                                theme.textTheme.titleSmall?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: theme.colorScheme.primary,
                                ),
                              ),
                            ),
                            Icon(
                              product.isAvailable
                                  ? Icons.check_circle
                                  : Icons.cancel,
                              color: product.isAvailable
                                  ? Colors.green
                                  : Colors.red,
                              size: 20,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),

            // 🔹 Bouton poubelle en haut à droite
            Positioned(
              top: 8,
              right: 8,
              child: IconButton(
                icon: Icon(Icons.delete_outline,
                    color: theme.colorScheme.primary),
                onPressed: () {
                  print("Delete product: ${product.id}");
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
