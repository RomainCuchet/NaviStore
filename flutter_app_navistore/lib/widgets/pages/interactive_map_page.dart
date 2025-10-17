import 'package:flutter/material.dart';
import '../../services/layout_api_service.dart';
import '../../models/layout_model.dart';
import '../common/interactive_map.dart';
import '../../repositories/shopping_list_repository.dart';

// Classe de base abstraite pour tous les pins
abstract class PinBase {
  final double x;
  final double y;
  final Color color;
  const PinBase({required this.x, required this.y, required this.color});
}

class MapPin extends PinBase {
  final String label;
  MapPin({
    required double x,
    required double y,
    required this.label,
    Color color = Colors.red,
  }) : super(x: x, y: y, color: color);
}

class ArticlePin extends PinBase {
  ArticlePin({
    required double x,
    required double y,
    Color color = Colors.blue,
  }) : super(x: x, y: y, color: color);
}

class _TrianglePainter extends CustomPainter {
  final Color color;

  _TrianglePainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final path = Path()
      ..moveTo(size.width / 2, size.height)
      ..lineTo(0, 0)
      ..lineTo(size.width, 0)
      ..close();

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

Widget buildArticlePin(ArticlePin pin, BuildContext context) {
  return Container(
    width: 18,
    height: 18,
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.primary,
      shape: BoxShape.circle,
      border: Border.all(color: Colors.white, width: 3),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withOpacity(0.2),
          blurRadius: 4,
          offset: const Offset(0, 1),
        ),
      ],
    ),
  );
}

class InteractiveMapPage extends StatefulWidget {
  final LayoutApiService layoutService;

  const InteractiveMapPage({Key? key, required this.layoutService})
      : super(key: key);

  @override
  State<InteractiveMapPage> createState() => _InteractiveMapPageState();
}

class _InteractiveMapPageState extends State<InteractiveMapPage>
    with AutomaticKeepAliveClientMixin<InteractiveMapPage> {
  @override
  bool get wantKeepAlive => true;

  late ShoppingListsRepository repo;

  String? _baseSvg;
  List<List<double>>? _optimizedPath;
  List<PinBase> _pins = [];
  int _svgVersion = 0;
  bool _loading = true;
  String? _error;
  String? _pathError;

  @override
  void initState() {
    super.initState();
    repo = ShoppingListsRepository();
    _initAndOptimize();
  }

  Future<void> _initAndOptimize() async {
    setState(() {
      _loading = true;
      _error = null;
      _pathError = null;
    });

    try {
      final fromHive = await LayoutModel.getFromHive();
      final baseSvg = (fromHive != null && fromHive.layoutSvg.isNotEmpty)
          ? fromHive.layoutSvg
          : '';

      List<List<double>>? pathData;
      List<PinBase> pins = [];

      // Calculer le chemin optimisé
      try {
        const List<double> startPoint = [9980.0, 5020.0];
        final rawPositions =
            await ShoppingListsRepository.fetchProductPositions();
        final poiCoordinates = <List<double?>>[];
        poiCoordinates.add([startPoint[0], startPoint[1]]);

        for (final p in rawPositions) {
          if (p.length >= 2 && p[0] != null && p[1] != null) {
            poiCoordinates.add([p[0], p[1]]);
          }
        }

        if (poiCoordinates.length >= 2) {
          final result = await widget.layoutService.optimizePath(
            poiCoordinates: poiCoordinates,
            includeReturnToStart: false,
          );

          if ((result['success'] == true) && result['complete_path'] is List) {
            pathData = (result['complete_path'] as List)
                .whereType<List>()
                .map<List<double>>((pt) {
              final x = (pt.isNotEmpty ? pt[0] : null);
              final y = (pt.length > 1 ? pt[1] : null);
              return [
                (x is num) ? x.toDouble() : 0.0,
                (y is num) ? y.toDouble() : 0.0,
              ];
            }).toList();
          }

          // Créer des pins pour chaque POI
          for (int i = 0; i < poiCoordinates.length; i++) {
            if (i == 0) {
              pins.add(MapPin(
                x: poiCoordinates[i][0]!,
                y: poiCoordinates[i][1]!,
                label: 'E',
                color: Theme.of(context).colorScheme.secondary,
              ));
            } else {
              pins.add(ArticlePin(
                x: poiCoordinates[i][0]!,
                y: poiCoordinates[i][1]!,
                color: Theme.of(context).colorScheme.primary,
              ));
            }
          }
        }
      } catch (e) {
        _pathError = 'Chemin non disponible: $e';
      }

      setState(() {
        _baseSvg = baseSvg;
        _optimizedPath = pathData;
        _pins = pins;
        _svgVersion++;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Erreur de chargement du plan: $e';
        _baseSvg = '';
        _loading = false;
      });
    }
  }

  String _createSvgWithPath(String baseSvg, List<List<double>> path) {
    if (baseSvg.isEmpty || path.isEmpty) return baseSvg;

    final points = path.map((pt) => '${pt[0]},${pt[1]}').join(' ');
    final overlay = '''
<!-- Optimized Path Overlay -->
<g id="optimized-path">
  <polyline points="$points" fill="none" stroke="#1E88E5" stroke-opacity="0.35" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="$points" fill="none" stroke="#64B5F6" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
</g>
''';

    final closeTag = '</svg>';
    final idx = baseSvg.lastIndexOf(closeTag);
    if (idx != -1) {
      return baseSvg.substring(0, idx) + overlay + closeTag;
    }
    return baseSvg + overlay;
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);

    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // En-tête
            Padding(
              padding:
                  const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
              child: Row(
                children: [
                  Text(
                    'Plan interactif',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: () async {
                      try {
                        await _initAndOptimize();
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Échec mise à jour: $e')),
                          );
                        }
                      }
                    },
                    tooltip: 'Rafraîchir',
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
            ),

            // Carte interactive
            Expanded(
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8.0),
                child: Card(
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Stack(
                      children: [
                        if (_loading)
                          const Center(
                              child: CircularProgressIndicator.adaptive())
                        else
                          InteractiveMap(
                            key: ValueKey('map-$_svgVersion'),
                            loadSvg: () async {
                              String svg = _baseSvg ?? '';
                              // Ajouter le chemin au SVG si disponible
                              if (_optimizedPath != null &&
                                  _optimizedPath!.isNotEmpty) {
                                svg = _createSvgWithPath(svg, _optimizedPath!);
                              }
                              return svg;
                            },
                            backgroundColor:
                                Theme.of(context).colorScheme.surfaceVariant,
                            // Builder pour les overlays (pins)
                            overlayBuilder: (svgToScreen) {
                              return Stack(
                                children: _pins.map((pin) {
                                  final screenPos = svgToScreen(pin.x, pin.y);
                                  if (pin is ArticlePin) {
                                    // Centrer le cercle sur la position
                                    return Positioned(
                                      left: screenPos.dx - 9,
                                      top: screenPos.dy - 9,
                                      child: _buildPin(pin),
                                    );
                                  } else {
                                    // MapPin : pointe du triangle exactement sur la position
                                    return Positioned(
                                      left: screenPos.dx - 20,
                                      top: screenPos.dy - 50,
                                      child: _buildPin(pin),
                                    );
                                  }
                                }).toList(),
                              );
                            },
                          ),

                        // Erreur de chemin (non-bloquante)
                        if (_pathError != null && !_loading)
                          Positioned(
                            left: 12,
                            top: 12,
                            right: 12,
                            child: Material(
                              color: Colors.transparent,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 8),
                                decoration: BoxDecoration(
                                  color: Theme.of(context)
                                      .colorScheme
                                      .errorContainer
                                      .withOpacity(0.9),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Row(
                                  children: [
                                    Icon(Icons.info_outline,
                                        size: 16,
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onErrorContainer),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        _pathError!,
                                        style: TextStyle(
                                          color: Theme.of(context)
                                              .colorScheme
                                              .onErrorContainer,
                                        ),
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),

                        // Erreur bloquante
                        if (_error != null && !_loading)
                          Positioned.fill(
                            child: Center(
                              child: Padding(
                                padding: const EdgeInsets.all(16.0),
                                child:
                                    Text(_error!, textAlign: TextAlign.center),
                              ),
                            ),
                          ),

                        // Bouton d'aide
                        Positioned(
                          right: 12,
                          bottom: 12,
                          child: FloatingActionButton(
                            heroTag: 'map-help',
                            elevation: 4,
                            mini: true,
                            backgroundColor:
                                Theme.of(context).colorScheme.primary,
                            onPressed: () {
                              showModalBottomSheet(
                                context: context,
                                shape: const RoundedRectangleBorder(
                                  borderRadius: BorderRadius.vertical(
                                    top: Radius.circular(16),
                                  ),
                                ),
                                builder: (ctx) {
                                  return Padding(
                                    padding: const EdgeInsets.all(16.0),
                                    child: Column(
                                      mainAxisSize: MainAxisSize.min,
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          'Aide',
                                          style: Theme.of(context)
                                              .textTheme
                                              .titleMedium,
                                        ),
                                        const SizedBox(height: 8),
                                        const Text(
                                          '• Pincez pour zoomer\n'
                                          '• Glissez pour naviguer\n'
                                          '• Double-tapez pour zoom/reset\n'
                                          '• Les pins rouges indiquent les produits',
                                        ),
                                        const SizedBox(height: 12),
                                      ],
                                    ),
                                  );
                                },
                              );
                            },
                            child: const Icon(Icons.info_outline),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPin(PinBase pin) {
    if (pin is MapPin) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: pin.color,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 3),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.3),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Center(
              child: Text(
                pin.label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          CustomPaint(
            size: const Size(10, 10),
            painter: _TrianglePainter(color: pin.color),
          ),
        ],
      );
    } else if (pin is ArticlePin) {
      return buildArticlePin(pin, context);
    }
    return const SizedBox.shrink();
  }
}
