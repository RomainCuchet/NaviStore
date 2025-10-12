import 'package:hive/hive.dart';

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

  ShoppingListModel({
    required this.id,
    required this.name,
    required this.productIds,
  });

  factory ShoppingListModel.fromJson(Map<String, dynamic> json) {
    return ShoppingListModel(
      id: json['id'] as String,
      name: json['name'] as String,
      productIds: (json['productIds'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'productIds': productIds,
    };
  }

  Future<void> saveToHive() async {
    final box = await Hive.openBox<ShoppingListModel>('shopping_lists');
    await box.put(id, this);
  }

  Future<void> deleteFromHive() async {
    final box = await Hive.openBox<ShoppingListModel>('shopping_lists');
    await box.delete(id);
  }

  static Future<List<ShoppingListModel>> getAllFromHive() async {
    final box = await Hive.openBox<ShoppingListModel>('shopping_lists');
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
  }) {
    return ShoppingListModel(
      id: id,
      name: name ?? this.name,
      productIds: productIds ?? this.productIds,
    );
  }
}
