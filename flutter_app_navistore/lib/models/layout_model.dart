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

  static Future<void> saveToHive(LayoutModel layout) async {
    var box = await Hive.openBox<LayoutModel>('layout');
    await box.put('current', layout);
  }

  static Future<LayoutModel?> getFromHive() async {
    var box = await Hive.openBox<LayoutModel>('layout');
    return box.get('current');
  }

  static Future<void> deleteFromHive() async {
    var box = await Hive.openBox<LayoutModel>('layout');
    await box.clear();
  }
}
