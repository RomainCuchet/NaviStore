import 'package:hive/hive.dart';
import '../models/product_model.dart';
import '../models/shopping_list_model.dart';

class ShoppingListRepository {
  static const _boxName = 'shopping_lists';

  Future<Box<ShoppingListModel>> _openBox() async {
    return Hive.openBox<ShoppingListModel>(_boxName);
  }

  /// Récupérer toutes les listes
  Future<List<ShoppingListModel>> getAllLists() async {
    final box = await _openBox();
    return box.values.toList();
  }

  /// Ajouter une nouvelle liste
  Future<void> addShoppingList(ShoppingListModel list) async {
    final box = await _openBox();
    await box.put(list.id, list);
  }

  /// Supprimer une liste
  Future<void> deleteShoppingList(String id) async {
    final box = await _openBox();
    await box.delete(id);
  }

  /// Ajouter un produit à une liste existante
  Future<void> addProductToList(String listId, ProductModel product) async {
    final box = await _openBox();
    final list = box.get(listId);
    if (list != null) {
      list.products.add(product);
      await list.save();
    }
  }

  /// Supprimer un produit d'une liste
  Future<void> removeProductFromList(
      String listId, ProductModel product) async {
    final box = await _openBox();
    final list = box.get(listId);
    if (list != null) {
      list.products.removeWhere((p) => p.id == product.id);
      await list.save();
    }
  }

  /// Mettre à jour la liste entière (produits + nom si besoin)
  Future<void> updateShoppingList(ShoppingListModel updatedList) async {
    final box = await _openBox();
    await box.put(updatedList.id, updatedList);
  }

  /// Récupérer les produits pour une liste
  Future<List<ProductModel>> getProductsForList(String listId) async {
    final box = await _openBox();
    final list = box.get(listId);
    return list?.products ?? [];
  }
}
