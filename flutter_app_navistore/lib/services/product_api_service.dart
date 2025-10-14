import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product_model.dart';

class ProductApiService {
  final String baseUrl;
  final String apiKey;

  ProductApiService({required this.baseUrl, required this.apiKey});

  Map<String, String> get _headers => {
        'x-api-key': apiKey,
      };

  Future<List<ProductModel>> getProducts({
    String? title,
    String? brand,
    String? category,
  }) async {
    final uri = Uri.parse('${baseUrl}/products/get').replace(queryParameters: {
      if (title != null && title.isNotEmpty) 'title': title,
      if (brand != null && brand.isNotEmpty) 'brand': brand,
      if (category != null && category.isNotEmpty) 'category': category,
    });

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode != 200) {
      throw Exception('Failed to load products: ${response.statusCode}');
    }

    final decoded = jsonDecode(response.body);

    if (decoded is Map<String, dynamic> && decoded.containsKey('results')) {
      final List<dynamic> data = decoded['results'];
      return data.map((json) => ProductModel.fromJson(json)).toList();
    } else {
      throw Exception('Unexpected API response format');
    }
  }

  Future<List<ProductModel>> getProductsByIds(List<String> ids) async {
    final uri = Uri.parse('$baseUrl/products/get_by_ids').replace(
      queryParameters: {
        'ids': ids, // 👈 pass as list, backend will parse ?ids=1&ids=2
      },
    );

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);

      if (decoded is Map<String, dynamic> && decoded.containsKey('results')) {
        final List<dynamic> data = decoded['results'];
        return data.map((json) => ProductModel.fromJson(json)).toList();
      } else {
        throw Exception('Unexpected API response format: $decoded');
      }
    } else {
      throw Exception(
        'Failed to load products by ids: ${response.statusCode} ${response.body}',
      );
    }
  }

  Future<List<String>> fetchCategories() async {
    final uri = Uri.parse('$baseUrl/products/get_categories');

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);
      final List results = data['results'];
      return List<String>.from(results);
    } else {
      throw Exception(
          'Failed to load categories: ${response.statusCode} ${response.body}');
    }
  }
}
