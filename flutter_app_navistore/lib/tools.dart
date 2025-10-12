import 'package:hive_flutter/hive_flutter.dart';

Future<void> deleteHiveBox(String boxName) async {
  if (Hive.isBoxOpen(boxName)) {
    await Hive.box(boxName).clear(); // vide la box
    await Hive.box(boxName).close();
  }
  await Hive.deleteBoxFromDisk(boxName); // supprime le fichier sur disque
}
