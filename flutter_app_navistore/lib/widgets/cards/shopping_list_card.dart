import 'package:flutter/material.dart';
import '../../models/product.dart';
import '../../services/product_service.dart';
import 'shopping_list_extended_card.dart';

class ShoppingListCard extends StatelessWidget {
  final String name;
  final IconData icon;
  final List<String> ids;

  const ShoppingListCard({
    Key? key,
    required this.name,
    required this.icon,
    required this.ids,
  }) : super(key: key);

  Future<void> _openExtendedCard(BuildContext context) async {
    try {
      // TODO: real API call to implement:
      // final productService = ProductService(baseUrl: "https://monapi.com");
      // final products = await productService.fetchProductsByIds(ids);

      // MOCK data for now
      final products = [
        Product(
          id: "p1",
          name: "Pommes Gala",
          isAvailable: true,
          brand: "Nature Fruits",
          category: "Fruits",
          price: 2.49,
          imagePath: "assets/images/pommes.jpg",
        ),
        Product(
          id: "p2",
          name: "Pâtes bio",
          isAvailable: false,
          brand: "Itali Market",
          category: "Épicerie",
          price: 1.59,
          imagePath: "assets/images/pates.jpg",
        ),
        Product(
          id: "p3",
          name: "Yaourt nature",
          isAvailable: true,
          brand: "Lactomia",
          category: "Produits laitiers",
          price: 1.89,
          imagePath: "assets/images/yaourt.jpg",
        ),
        Product(
          id: "p3",
          name: "Yaourt nature",
          isAvailable: true,
          brand: "Lactomia",
          category: "Produits laitiers",
          price: 1.89,
          imagePath: "assets/images/yaourt.jpg",
        ),
        Product(
          id: "p3",
          name: "Yaourt nature",
          isAvailable: true,
          brand: "Lactomia",
          category: "Produits laitiers",
          price: 1.89,
          imagePath: "assets/images/yaourt.jpg",
        ),
        Product(
          id: "p3",
          name: "Yaourt nature",
          isAvailable: true,
          brand: "Lactomia",
          category: "Produits laitiers",
          price: 1.89,
          imagePath: "assets/images/yaourt.jpg",
        ),
        Product(
          id: "p3",
          name: "Yaourt nature",
          isAvailable: true,
          brand: "Lactomia",
          category: "Produits laitiers",
          price: 1.89,
          imagePath: "assets/images/yaourt.jpg",
        ),
        Product(
          id: "p3",
          name: "Yaourt nature",
          isAvailable: false,
          brand: "",
          category: "",
          price: 0,
          imagePath: "assets/images/yaourt.jpg",
        ),
      ];

      // ✅ Une fois récupérés (API ou mock), on affiche l’extended card
      Navigator.of(context).push(
        PageRouteBuilder(
          opaque: false, // pour l’overlay
          pageBuilder: (_, __, ___) => ShoppingListExtendedCard(
            listName: name,
            products: products,
          ),
        ),
      );
    } catch (e) {
      // Error Handeling (API down, parsing, etc.)
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
