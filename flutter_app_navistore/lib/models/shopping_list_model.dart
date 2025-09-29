import 'package:hive/hive.dart';
import 'product_model.dart';

part 'shopping_list_model.g.dart';

@HiveType(typeId: 0)
class ShoppingListModel extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String name;

  @HiveField(2)
  final List<ProductModel> products;

  ShoppingListModel({
    required this.id,
    required this.name,
    required this.products,
  });

  factory ShoppingListModel.fromJson(Map<String, dynamic> json) {
    return ShoppingListModel(
      id: json['id'] as String,
      name: json['name'] as String,
      products: (json['products'] as List)
          .map((e) => ProductModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'products': products.map((p) => p.toJson()).toList(),
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
}
