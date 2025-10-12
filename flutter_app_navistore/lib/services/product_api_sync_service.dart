import 'package:hive/hive.dart';
import '../models/product_model.dart';
import '../models/shopping_list_model.dart';
import '../services/product_api_service.dart';

class ProductApiSyncService {
  final ProductApiService api;

  ProductApiSyncService(this.api);

  /// Charge et synchronise tous les produits stockés localement avec l'API
  Future<void> syncProducts(List<ShoppingListModel> lists) async {
    final allProductsBox = await Hive.openBox<ProductModel>('products');

    final storedProducts = allProductsBox.values.toList();

    // Récupère tous les IDs des produits utilisés dans les listes
    final allIdsInLists = lists.expand((l) => l.productIds).toSet();

    try {
      // Appel API avec List<String>
      final fetchedProducts =
          await api.getProductsByIds(allIdsInLists.toList());

      final fetchedMap = {for (var p in fetchedProducts) p.id: p};

      for (var stored in storedProducts) {
        if (fetchedMap.containsKey(stored.id)) {
          final updated = fetchedMap[stored.id]!.copyWith(isAvailable: true);
          await updated.saveToHive();
        } else if (allIdsInLists.contains(stored.id)) {
          final updated = stored.copyWith(isAvailable: false);
          await updated.saveToHive();
        }
      }

      for (var p in fetchedProducts) {
        if (!storedProducts.any((sp) => sp.id == p.id)) {
          await p.saveToHive();
        }
      }

      for (var stored in storedProducts) {
        if (!allIdsInLists.contains(stored.id)) {
          await stored.deleteFromHive();
        }
      }
    } catch (e) {
      print(
          "❌ API offline, les produits existants restent avec isAvailable = false");
      for (var stored in storedProducts) {
        if (allIdsInLists.contains(stored.id)) {
          final updated = stored.copyWith(isAvailable: false);
          await updated.saveToHive();
        }
      }
    }
  }
}
