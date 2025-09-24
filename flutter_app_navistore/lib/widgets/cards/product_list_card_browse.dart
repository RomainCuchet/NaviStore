import 'package:flutter/material.dart';
import '../../models/product_model.dart';

class ProductListCardBrowse extends StatelessWidget {
  final ProductModel product;
  final VoidCallback onTap;
  final VoidCallback onAddToList;

  const ProductListCardBrowse({
    super.key,
    required this.product,
    required this.onTap,
    required this.onAddToList,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      margin: const EdgeInsets.all(8),
      child: ListTile(
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.network(
            product.imagePath,
            width: 50,
            height: 50,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) =>
                const Icon(Icons.broken_image, size: 40),
          ),
        ),
        title: Text(product.name),
        subtitle: Text("${product.brand} • ${product.category}"),
        trailing: IconButton(
          icon: const Icon(Icons.playlist_add),
          onPressed: onAddToList,
        ),
        onTap: onTap,
      ),
    );
  }
}
