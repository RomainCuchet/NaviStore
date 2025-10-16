import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../models/shopping_list_model.dart';

import '../../repositories/shopping_list_repository.dart';

import '../cards/shopping_list_card.dart';

class ShoppingListsPage extends StatefulWidget {
  const ShoppingListsPage({super.key});

  @override
  State<ShoppingListsPage> createState() => _ShoppingListsPageState();
}

class _ShoppingListsPageState extends State<ShoppingListsPage> {
  late ShoppingListsRepository repo;

  @override
  void initState() {
    super.initState();
    repo = ShoppingListsRepository();
  }

  Future<void> _deleteList(BuildContext context, ShoppingListModel list) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Supprimer la liste ?"),
        content:
            Text("Voulez-vous vraiment supprimer la liste '${list.name}' ?"),
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
      await repo.deleteShoppingList(list.id);
    }
  }

  @override
  Widget build(BuildContext context) {
    final box = Hive.box<ShoppingListModel>('shopping_lists');

    return Scaffold(
      appBar: AppBar(title: const Text("Shopping Lists")),
      body: ValueListenableBuilder(
        valueListenable: box.listenable(),
        builder: (context, Box<ShoppingListModel> box, _) {
          final lists = box.values.toList();

          if (lists.isEmpty) {
            return const Center(child: Text('Aucune liste enregistrée'));
          }

          return GridView.builder(
            padding: const EdgeInsets.all(16),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
            ),
            itemCount: lists.length,
            itemBuilder: (_, index) {
              final list = lists[index];
              return ShoppingListCard(
                shoppingList: list,
                icon: Icons.list,
                onDelete: () => _deleteList(context, list),
              );
            },
          );
        },
      ),
    );
  }
}
