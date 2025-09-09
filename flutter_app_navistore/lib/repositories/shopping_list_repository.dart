import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/shopping_list.dart';

class ShoppingListRepository {
  static const _key = "shopping_lists";

  static Future<List<ShoppingList>> loadLists() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_key);

    if (data == null) return [];
    final List decoded = jsonDecode(data);

    return decoded.map((json) => ShoppingList.fromJson(json)).toList();
  }

  static Future<void> saveLists(List<ShoppingList> lists) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(lists.map((l) => l.toJson()).toList());
    await prefs.setString(_key, encoded);
  }

  static Future<void> addList(ShoppingList list) async {
    final lists = await loadLists();
    lists.add(list);
    await saveLists(lists);
  }

  static Future<void> removeList(String id) async {
    final lists = await loadLists();
    lists.removeWhere((l) => l.id == id);
    await saveLists(lists);
  }
}
