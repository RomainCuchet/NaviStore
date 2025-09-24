import 'package:hive/hive.dart';
import '../models/product_model.dart';
import '../models/shopping_list_model.dart';

class ShoppingListRepository {
  static const _boxName = 'shopping_lists';

  Future<Box<ShoppingListModel>> _openBox() async {
    return Hive.openBox<ShoppingListModel>(_boxName);
  }

  Future<List<ShoppingListModel>> getAllLists() async {
    final box = await _openBox();
    return box.values.toList();
  }

  Future<void> addShoppingList(ShoppingListModel list) async {
    final box = await _openBox();
    await box.put(list.id, list);
  }

  Future<void> deleteShoppingList(String id) async {
    final box = await _openBox();
    await box.delete(id);
  }

  Future<void> addProductToList(String listId, ProductModel product) async {
    final box = await _openBox();
    final list = box.get(listId);
    if (list != null) {
      final updated = ShoppingListModel(
        id: list.id,
        name: list.name,
        productIds: [...list.productIds, product.id],
      );
      await box.put(listId, updated);
    }
    // Sauvegarder le produit dans sa box si pas déjà
    final productBox = await Hive.openBox<ProductModel>('products');
    if (!productBox.containsKey(product.id)) {
      await productBox.put(product.id, product);
    }
  }

  Future<List<ProductModel>> getProductsForList(String listId) async {
    final box = await _openBox();
    final list = box.get(listId);
    if (list == null) return [];

    final productBox = await Hive.openBox<ProductModel>('products');
    return list.productIds
        .map((id) => productBox.get(id))
        .whereType<ProductModel>()
        .toList();
  }
}
