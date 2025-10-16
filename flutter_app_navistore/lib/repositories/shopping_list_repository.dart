import 'package:hive/hive.dart';
import '../models/shopping_list_model.dart';
import '../models/product_model.dart';

class ShoppingListsRepository {
  final String _boxName = 'shopping_lists';

  /// Ouvre la box Hive
  Future<Box<ShoppingListModel>> _getBox() async {
    return Hive.box<ShoppingListModel>(_boxName);
  }

  /// Récupérer toutes les listes
  Future<List<ShoppingListModel>> getAllShoppingLists() async {
    final box = await _getBox();
    return box.values.toList();
  }

  /// Ajouter une nouvelle liste
  Future<void> addShoppingList(ShoppingListModel shoppingList) async {
    final box = await _getBox();
    await box.put(shoppingList.id, shoppingList);
  }

  /// Mettre à jour une liste existante
  Future<void> updateShoppingList(ShoppingListModel shoppingList) async {
    final box = await _getBox();
    await box.put(shoppingList.id, shoppingList);
  }

  /// Supprimer une liste
  Future<void> deleteShoppingList(String id) async {
    final box = await _getBox();
    await box.delete(id);
  }

  /// Ajouter un produit à une liste
  Future<void> addProductToList(String listId, String productId) async {
    final box = await _getBox();
    final list = box.get(listId);
    if (list != null) {
      final updated = list.copyWith(
        productIds: [...list.productIds, productId],
      );
      await box.put(listId, updated);
    }
  }

  /// Supprimer un produit d’une liste
  Future<void> removeProductFromList(String listId, String productId) async {
    final box = await _getBox();
    final list = box.get(listId);
    if (list != null) {
      final updated = list.copyWith(
        productIds: list.productIds.where((id) => id != productId).toList(),
      );
      await box.put(listId, updated);
    }
  }

  /// Supprimer toutes les listes
  Future<void> clearAllLists() async {
    final box = await _getBox();
    await box.clear();
  }

  static Future<void> cleanOrphanedProducts() async {
    final allLists = await ShoppingListModel.getAllFromHive();
    final allProductIdsInLists =
        allLists.expand((list) => list.productIds).toSet();

    final productsBox = await Hive.box<ProductModel>('products');
    final allStoredProducts = productsBox.values.toList();

    for (var product in allStoredProducts) {
      if (!allProductIdsInLists.contains(product.id)) {
        await productsBox.delete(product.id);
      }
    }
  }
}
