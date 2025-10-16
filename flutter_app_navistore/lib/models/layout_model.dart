import 'package:hive/hive.dart';

part 'layout_model.g.dart';

@HiveType(typeId: 2)
class LayoutModel extends HiveObject {
  @HiveField(0)
  final String layoutHash;

  @HiveField(1)
  final String layoutSvg; // SVG data as a string

  LayoutModel({
    required this.layoutHash,
    required this.layoutSvg,
  });

  /// Save the single object to Hive (overwrite if exists)
  static Future<void> saveToHive(LayoutModel layout) async {
    var box = Hive.box<LayoutModel>('layout');
    await box.put('single', layout);
  }

  /// Retrieve the single object from Hive
  static Future<LayoutModel?> getFromHive() async {
    var box = Hive.box<LayoutModel>('layout');
    return box.get('single');
  }

  /// Delete the single object from Hive
  static Future<void> deleteFromHive() async {
    var box = Hive.box<LayoutModel>('layout');
    await box.clear();
  }
}
