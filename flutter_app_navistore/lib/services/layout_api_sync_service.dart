import 'package:hive/hive.dart';
import '../models/layout_model.dart';
import '../services/layout_api_service.dart';

class LayoutApiSyncService {
  final LayoutApiService api;

  LayoutApiSyncService({
    required this.api,
  });

  /// Load and synchronize the locally stored layout with the API
  Future<void> syncLayout() async {
    final storedLayout = await LayoutModel.getFromHive();

    final apiLayoutHash = await api.getLayoutHash();

    // If the hash is different, fetch the new SVG and update local storage
    if (storedLayout == null || storedLayout.layoutHash != apiLayoutHash) {
      // Delete previous layout if exists
      await LayoutModel.deleteFromHive();

      final newLayout = LayoutModel(
        layoutHash: apiLayoutHash,
        layoutSvg: await api.getLayoutSvg(),
      );
      await LayoutModel.saveToHive(newLayout);
      print("✅ Layout updated from API");
    } else {
      print("ℹ️ Layout is up to date");
    }
  }
}
