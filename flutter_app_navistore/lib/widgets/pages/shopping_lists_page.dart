import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../cards/shopping_list_card.dart';
import '../../models/shopping_list_model.dart';
import '../../models/product_model.dart';

class ShoppingListsPage extends StatefulWidget {
  const ShoppingListsPage({super.key});

  @override
  State<ShoppingListsPage> createState() => _ShoppingListsPageState();
}

class _ShoppingListsPageState extends State<ShoppingListsPage> {
  late Box<ShoppingListModel> shoppingListBox;
  late Box<ProductModel> productBox;

  @override
  void initState() {
    super.initState();
    shoppingListBox = Hive.box<ShoppingListModel>('shopping_lists');
    productBox = Hive.box<ProductModel>('products');
  }

  List<ProductModel> _getProductsForList(List<String> ids) {
    return ids
        .map((id) => productBox.get(id))
        .whereType<ProductModel>() // filtre les nulls
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final lists = shoppingListBox.values.toList();

    if (lists.isEmpty) {
      return const Center(child: Text('Aucune liste enregistrée'));
    }

    return GridView.count(
      padding: const EdgeInsets.all(16),
      crossAxisCount: 2,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      children: lists.map((list) {
        final products = _getProductsForList(list.productIds);
        return ShoppingListCard(
          name: list.name,
          icon: Icons.list,
          ids: list.productIds,
          products: products,
        );
      }).toList(),
    );
  }
}
