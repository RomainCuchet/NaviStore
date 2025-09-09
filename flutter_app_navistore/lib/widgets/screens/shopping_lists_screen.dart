import 'package:flutter/material.dart';
import '../cards/shopping_list_card.dart';

class ShoppingListsScreen extends StatelessWidget {
  const ShoppingListsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Exemple de données mockées
    final lists = [
      {
        "name": "Food",
        "icon": Icons.food_bank,
        "ids": ["p1", "p2", "p3"],
      },
      {
        "name": "Bricolage",
        "icon": Icons.build,
        "ids": ["b1"],
      },
      {
        "name": "Cuisine",
        "icon": Icons.restaurant,
        "ids": ["c1", "c2"],
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text("Shopping Lists"),
      ),
      body: GridView.count(
        padding: const EdgeInsets.all(16),
        crossAxisCount: 2,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
        children: lists
            .map((list) => ShoppingListCard(
                  name: list["name"] as String,
                  icon: list["icon"] as IconData,
                  ids: list["ids"] as List<String>,
                ))
            .toList(),
      ),
    );
  }
}
