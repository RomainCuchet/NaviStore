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
  late Future<List<ShoppingListModel>> _listsFuture;
  late Future<List<ProductModel>> _productsFuture;

  @override
  void initState() {
    super.initState();
    _productsFuture = ProductModel.getAllFromHive();
    _listsFuture = ShoppingListModel.getAllFromHive();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Shopping Lists")),
      body: FutureBuilder<List<ShoppingListModel>>(
        future: _listsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Erreur: ${snapshot.error}'));
          }

          final lists = snapshot.data ?? [];

          if (lists.isEmpty) {
            return const Center(child: Text('Aucune liste enregistrée'));
          }

          return GridView.count(
            padding: const EdgeInsets.all(16),
            crossAxisCount: 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            children: lists
                .map((list) => ShoppingListCard(
                      name: list.name,
                      icon: Icons.list, // tu peux customiser selon la liste
                      ids: list.productIds,
                    ))
                .toList(),
          );
        },
      ),
    );
  }
}
