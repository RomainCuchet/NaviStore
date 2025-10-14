import 'package:hive/hive.dart';

part 'product_categories_model.g.dart';

@HiveType(typeId: 4)
class ProductCategoriesModel extends HiveObject {
  @HiveField(0)
  final List<String> productCategories;

  ProductCategoriesModel({
    required this.productCategories,
  }) {
    productCategories
        .sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));
  }

  /// Save the single object to Hive (overwrite if exists)
  static Future<void> saveToHive(ProductCategoriesModel model) async {
    var box =
        await Hive.openBox<ProductCategoriesModel>('productCategoriesBox');
    await box.put('single', model);
  }

  /// Retrieve the single object from Hive, or an empty one if none exists
  static Future<ProductCategoriesModel> getFromHive() async {
    var box =
        await Hive.openBox<ProductCategoriesModel>('productCategoriesBox');
    var model = box.get('single');
    return model ?? ProductCategoriesModel(productCategories: []);
  }

  /// Delete the single object from Hive
  static Future<void> deleteFromHive() async {
    var box =
        await Hive.openBox<ProductCategoriesModel>('productCategoriesBox');
    await box.delete('single');
  }
}
