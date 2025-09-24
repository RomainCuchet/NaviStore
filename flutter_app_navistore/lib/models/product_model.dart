import 'package:hive/hive.dart';

part 'product_model.g.dart';

@HiveType(typeId: 1)
class ProductModel extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String name;

  @HiveField(2)
  final bool isAvailable;

  @HiveField(3)
  final String brand;

  @HiveField(4)
  final String category;

  @HiveField(5)
  final double price;

  @HiveField(6)
  final String imagePath;

  ProductModel({
    required this.id,
    required this.name,
    this.isAvailable = false,
    this.brand = '',
    this.category = '',
    this.price = 0.0,
    this.imagePath = '',
  });

  factory ProductModel.fromJson(Map<String, dynamic> json) {
    return ProductModel(
      id: json['id'].toString(),
      name: json['title'] ?? '',
      brand: json['brand'] ?? '',
      category: json['category'] ?? '',
      price: (json['first_product_price'] as num?)?.toDouble() ?? 0.0,
      imagePath: json['image_url'] ?? '',
      isAvailable: true, // ou calculé selon ton API
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'isAvailable': isAvailable,
      'brand': brand,
      'category': category,
      'price': price,
      'image': imagePath,
    };
  }

  Future<void> saveToHive() async {
    final box = await Hive.openBox<ProductModel>('products');
    await box.put(id, this);
  }

  Future<void> deleteFromHive() async {
    final box = await Hive.openBox<ProductModel>('products');
    await box.delete(id);
  }

  static Future<List<ProductModel>> getAllFromHive() async {
    final box = await Hive.openBox<ProductModel>('products');
    return box.values.toList();
  }
}
