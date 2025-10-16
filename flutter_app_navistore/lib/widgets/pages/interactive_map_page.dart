import 'package:flutter/material.dart';
import '../../services/layout_api_service.dart';
import '../../models/layout_model.dart';
import '../common/interactive_map.dart';
import '../../repositories/shopping_list_repository.dart';

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
  bool get wantKeepAlive =>
      true; // garde l'état de la page entre les navigations

  late ShoppingListsRepository repo;

  String? _baseSvg;
  String? _svgWithPath;
  int _svgVersion = 0; // change key to force InteractiveMap to reload
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

    // Always try to load the base SVG; if this fails, we show an error.
    try {
      final fromHive = await LayoutModel.getFromHive();
      final baseSvg = (fromHive != null && fromHive.layoutSvg.isNotEmpty)
          ? fromHive.layoutSvg
          : '';

      // Prepare initial state to display at least the base map
      String svgWithPath = baseSvg;

      // Try to compute optimized path, but don't block the map if it fails
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
            final path = (result['complete_path'] as List)
                .whereType<List>()
                .map<List<double>>((pt) {
              final x = (pt.isNotEmpty ? pt[0] : null);
              final y = (pt.length > 1 ? pt[1] : null);
              return [
                (x is num) ? x.toDouble() : 0.0,
                (y is num) ? y.toDouble() : 0.0,
              ];
            }).toList();
            svgWithPath = _injectPathIntoSvg(baseSvg, path);
          }
        }
      } catch (e) {
        // Keep map visible; just remember the path error
        _pathError = 'Chemin non disponible: $e';
      }

      setState(() {
        _baseSvg = baseSvg;
        _svgWithPath = svgWithPath;
        _svgVersion++;
        _loading = false;
      });
    } catch (e) {
      // Base map failed to load; show an error message but avoid crashing
      setState(() {
        _error = 'Erreur de chargement du plan: $e';
        _baseSvg = '';
        _svgWithPath = '';
        _loading = false;
      });
    }
  }

  String _injectPathIntoSvg(String svg, List<List<double>> path) {
    if (svg.isEmpty || path.isEmpty) return svg;

    // Build points attribute: "x1,y1 x2,y2 ..."
    final points = path.map((pt) => '${pt[0]},${pt[1]}').join(' ');

    // Two-layer polyline for a modern look (base glow + top line)
    final overlay = '''
<!-- Optimized Path Overlay -->
<g id="optimized-path">
  <polyline points="$points" fill="none" stroke="#1E88E5" stroke-opacity="0.35" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="$points" fill="none" stroke="#64B5F6" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
</g>
''';

    // Insert before closing root tag. Try to place just before </svg>
    final closeTag = '</svg>';
    final idx = svg.lastIndexOf(closeTag);
    if (idx != -1) {
      return svg.substring(0, idx) + overlay + closeTag;
    }
    // Fallback: append
    return svg + overlay;
  }

  @override
  Widget build(BuildContext context) {
    super.build(context); // obligatoire avec AutomaticKeepAliveClientMixin

    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // --- En-tête minimaliste ---
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
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Échec mise à jour: $e')),
                        );
                      }
                    },
                    tooltip: 'Rafraîchir',
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
            ),

            // --- Carte interactive ---
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
                              // Return base svg or svg with path if available
                              return _svgWithPath ?? _baseSvg ?? '';
                            },
                            backgroundColor:
                                Theme.of(context).colorScheme.surfaceVariant,
                          ),

                        // Non-blocking error hint if optimization failed
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

                        // Blocking error only if base map failed to load
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

                        // --- Bouton d'aide ---
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
                                          '• Double-tapez pour zoom/reset',
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
}
