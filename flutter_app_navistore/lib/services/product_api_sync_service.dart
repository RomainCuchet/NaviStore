import 'package:hive/hive.dart';

import '../models/product_model.dart';
import '../models/shopping_list_model.dart';
import '../models/product_categories_model.dart';

import '../services/product_api_service.dart';

class ProductApiSyncService {
  final ProductApiService api;

  ProductApiSyncService(this.api);

  /// Load and synchronize the locally stored product categories with the API
  Future<void> syncProductCategories() async {
    try {
      final categories = await api.fetchCategories();
      final categoriesModel = ProductCategoriesModel(
        productCategories: categories,
      );
      await ProductCategoriesModel.saveToHive(categoriesModel);
    } catch (e) {
      print("❌Error syncing product categories (Api disconnected ?): $e");
    }
  }

  /// Load and synchronize all locally stored products with the API
  Future<void> syncProducts() async {
    final allProductsBox = Hive.box<ProductModel>('products');
    final allListsBox = Hive.box<ShoppingListModel>('shopping_lists');

    final storedProducts = allProductsBox.values.toList();

    // Get all product IDs used in the lists
    final allIdsInLists =
        allListsBox.values.expand((l) => l.productIds).toSet();

    try {
      // Fetch only the products that are in the lists
      final fetchedProducts =
          await api.getProductsByIds(allIdsInLists.toList());

      final fetchedMap = {for (var p in fetchedProducts) p.id: p};

      // Update availability of all stored products according to fetched data
      for (var stored in storedProducts) {
        if (fetchedMap.containsKey(stored.id)) {
          final updated = fetchedMap[stored.id]!.copyWith(isAvailable: true);
          await updated.saveToHive();
        } else if (allIdsInLists.contains(stored.id)) {
          final updated = stored.copyWith(isAvailable: false);
          await updated.saveToHive();
        }
      }

      // Remove products that are no longer in any list
      for (var stored in storedProducts) {
        if (!allIdsInLists.contains(stored.id)) {
          await stored.deleteFromHive();
        }
      }
    } catch (e) {
      print("❌Error syncing products (Api disconnected ?): $e");
      for (var stored in storedProducts) {
        if (allIdsInLists.contains(stored.id)) {
          final updated = stored.copyWith(isAvailable: false);
          await updated.saveToHive();
        }
      }
    }
  }

  Future<void> fullResync() async {
    await syncProductCategories();
    await syncProducts();
  }
}
