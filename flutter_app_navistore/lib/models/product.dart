class Product {
  final String id;
  final String name;
  bool isAvailable;
  final String brand;
  final String category;
  final double price;
  final String imagePath;

  Product({
    required this.id,
    required this.name,
    this.isAvailable = false,
    this.brand = '',
    this.category = '',
    this.price = 0.0,
    this.imagePath = '',
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'] as String,
      name: json['name'] as String,
      brand: json['brand'] as String,
      category: json['category'] as String,
      price: (json['price'] as num).toDouble(),
      imagePath: json['image'] as String,
    );
  }
}
