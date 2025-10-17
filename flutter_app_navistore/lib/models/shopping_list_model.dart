import 'package:hive/hive.dart';
import 'product_model.dart';

part 'shopping_list_model.g.dart';

@HiveType(typeId: 0)
class ShoppingListModel extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String name;

  /// Stocke uniquement les IDs des produits
  @HiveField(2)
  final List<String> productIds;

  @HiveField(3)
  bool showInOtherView;

  ShoppingListModel({
    required this.id,
    required this.name,
    required this.productIds,
    this.showInOtherView = false,
  });

  factory ShoppingListModel.fromJson(Map<String, dynamic> json) {
    return ShoppingListModel(
      id: json['id'] as String,
      name: json['name'] as String,
      productIds: (json['productIds'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      showInOtherView: json['showInOtherView'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'productIds': productIds,
      'showInOtherView': showInOtherView,
    };
  }

  Future<void> saveToHive() async {
    final box = Hive.box<ShoppingListModel>('shopping_lists');
    await box.put(id, this);
  }

  Future<void> deleteFromHive() async {
    final box = Hive.box<ShoppingListModel>('shopping_lists');
    await box.delete(id);
  }

  static Future<List<ShoppingListModel>> getAllFromHive() async {
    final box = Hive.box<ShoppingListModel>('shopping_lists');
    return box.values.toList();
  }

  /// Ajoute un produit (par ID) à la liste
  Future<void> addProductId(String productId) async {
    if (!productIds.contains(productId)) {
      productIds.add(productId);
      await saveToHive();
    }
  }

  /// Retire un produit (par ID) de la liste
  Future<void> removeProductId(String productId) async {
    productIds.remove(productId);
    await saveToHive();
  }

  /// Copie avec modification des champs (utile pour repository)
  ShoppingListModel copyWith({
    String? name,
    List<String>? productIds,
    bool? showInOtherView,
  }) {
    return ShoppingListModel(
      id: id,
      name: name ?? this.name,
      productIds: productIds ?? this.productIds,
      showInOtherView: showInOtherView ?? this.showInOtherView,
    );
  }

  Future<List<ProductModel>> getProducts() async {
    final productsBox = Hive.box<ProductModel>('products');
    List<ProductModel> products = [];

    for (var productId in productIds) {
      final product = productsBox.get(productId);
      if (product != null) {
        products.add(product);
      }
    }

    return products;
  }

  Future<(double, double)> getPrices() async {
    final products = await getProducts();

    double totalProductsPrice = products.fold(0, (sum, p) => sum + p.price);
    double availableProductsPrice =
        products.where((p) => p.isAvailable).fold(0, (sum, p) => sum + p.price);

    return (totalProductsPrice, availableProductsPrice);
  }

  Future<(int, int)> getProductCounts() async {
    final products = await getProducts();

    int totalProductsCount = products.length;
    int availableProductsCount = products.where((p) => p.isAvailable).length;

    return (totalProductsCount, availableProductsCount);
  }
}
