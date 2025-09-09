class ShoppingList {
  final String id;
  final String name;
  final List<String> productIds;

  ShoppingList({
    required this.id,
    required this.name,
    required this.productIds,
  });

  Map<String, dynamic> toJson() => {
        "id": id,
        "name": name,
        "productIds": productIds,
      };

  factory ShoppingList.fromJson(Map<String, dynamic> json) {
    return ShoppingList(
      id: json["id"],
      name: json["name"],
      productIds: List<String>.from(json["productIds"]),
    );
  }
}
