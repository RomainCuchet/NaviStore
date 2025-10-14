import 'dart:convert';
import 'package:http/http.dart' as http;

class LayoutApiService {
  final String baseUrl;
  final String apiKey;

  LayoutApiService({required this.baseUrl, required this.apiKey});

  Map<String, String> get _headers => {
        'x-api-key': apiKey,
      };

  Future<String> getLayoutHash() async {
    final uri = Uri.parse('${baseUrl}/path_optimization/layout_hash');

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode != 200) {
      throw Exception('Failed to load layout hash: ${response.statusCode}');
    }

    final decoded = jsonDecode(response.body);

    if (decoded is Map<String, dynamic> && decoded.containsKey('layout_hash')) {
      return decoded['layout_hash'];
    } else {
      throw Exception('Unexpected API response format');
    }
  }

  Future<String> getLayoutSvg() async {
    final uri = Uri.parse('${baseUrl}/path_optimization/layout_svg');

    final response = await http.get(uri, headers: _headers);

    if (response.statusCode != 200) {
      throw Exception('Failed to load layout: ${response.statusCode}');
    }

    return response.body;
  }

  Future<Map<String, dynamic>> optimizePath(
      List<Map<String, double>> poiList) async {
    final uri = Uri.parse('${baseUrl}/path_optimization/optimize_path');

    final body = jsonEncode({
      'poi_list': poiList,
    });

    final response = await http.post(uri,
        headers: {..._headers, 'Content-Type': 'application/json'}, body: body);

    if (response.statusCode != 200) {
      throw Exception('Failed to optimize path: ${response.statusCode}');
    }

    final decoded = jsonDecode(response.body);

    if (decoded is Map<String, dynamic>) {
      return {
        'total_distance': decoded['total_distance'],
        'computation_time': decoded['computation_time'],
        'complete_path': decoded['complete_path'],
      };
    } else {
      throw Exception('Unexpected API response format');
    }
  }
}
