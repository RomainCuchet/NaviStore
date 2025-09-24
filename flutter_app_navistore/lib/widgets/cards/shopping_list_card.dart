import 'package:flutter/material.dart';
import '../../models/product_model.dart';
import 'shopping_list_extended_card.dart';

class ShoppingListCard extends StatelessWidget {
  final String name;
  final IconData icon;
  final List<String> ids;
  final List<ProductModel> products; // ✅ ajout

  const ShoppingListCard({
    Key? key,
    required this.name,
    required this.icon,
    required this.ids,
    required this.products, // ✅ ajout
  }) : super(key: key);

  Future<void> _openExtendedCard(BuildContext context) async {
    try {
      // Utilise maintenant les produits réels
      Navigator.of(context).push(
        PageRouteBuilder(
          opaque: false,
          pageBuilder: (_, __, ___) => ShoppingListExtendedCard(
            listName: name,
            products: products,
          ),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Impossible de charger les produits : $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _openExtendedCard(context),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircleAvatar(
                radius: 32,
                backgroundColor: theme.colorScheme.primaryContainer,
                child: Icon(
                  icon,
                  size: 32,
                  color: theme.colorScheme.onPrimaryContainer,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                name,
                textAlign: TextAlign.center,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                "${ids.length} produit${ids.length > 1 ? 's' : ''}",
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
