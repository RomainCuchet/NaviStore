import 'package:hive/hive.dart';

part 'shopping_list_model.g.dart';

@HiveType(typeId: 0)
class ShoppingListModel extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String name;

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
      productIds: List<String>.from(json['productIds'] as List),
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
}
