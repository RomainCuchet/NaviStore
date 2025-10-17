import 'package:flutter/material.dart';
import '../../services/layout_api_service.dart';
import '../../models/layout_model.dart';
import '../map/interactive_map.dart';
import '../../repositories/shopping_list_repository.dart';
import '../map/map_overlays.dart';
import '../map/buble_pin_product_info.dart';

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

// Widget d'indicateur moderne

// Widget d'indicateur moderne

class InteractiveMapPage extends StatefulWidget {
  final LayoutApiService layoutService;

  const InteractiveMapPage({Key? key, required this.layoutService})
      : super(key: key);

  @override
  State<InteractiveMapPage> createState() => _InteractiveMapPageState();
}

class _InteractiveMapPageState extends State<InteractiveMapPage>
    with AutomaticKeepAliveClientMixin<InteractiveMapPage> {
  ProductPin? _selectedProductPin;
  Offset? _selectedPinScreenPos;
  bool _showInfoBar = true;

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
  double _totalDistance = 0.0;

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
            includeReturnToStart: true,
          );

          // Stocker la distance totale
          _totalDistance =
              (result['total_distance'] as num?)?.toDouble() ?? 0.0;

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

          // add starting point pin
          pins.add(
              RoundPin(x: poiCoordinates[0][0]!, y: poiCoordinates[0][1]!));
        }

        //create pins for products
        ShoppingListsRepository.fetchMapProducts().then((products) {
          for (var i = 0; i < products.length; i++) {
            final product = products[i];
            final pos = product.position;
            if (pos != null && pos.length >= 2) {
              pins.add(ProductPin(
                x: pos[0].toDouble(),
                y: pos[1].toDouble(),
                imagePath: product.imagePath ?? '',
                name: product.name,
                price: product.price,
                color: Theme.of(context).colorScheme.primary,
              ));
            }
          }
        });
      } catch (e) {
        _pathError = 'Unavailable path: $e';
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
        _error = 'Error loading map: $e';
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
  <polyline points="$points" fill="none" stroke="#6f65ad" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>
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
            // Thin modern header bar
            Container(
              height: 38,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface.withOpacity(0.95),
                border: const Border(
                  bottom: BorderSide(width: 0.5, color: Color(0x11000000)),
                ),
              ),
              child: Row(
                children: [
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
                    icon: const Icon(Icons.refresh, size: 22),
                    splashRadius: 18,
                  ),
                  const Spacer(),
                  // Modern toggle (radio) button for info section
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 200),
                    child: Switch(
                      value: _showInfoBar,
                      onChanged: (val) {
                        setState(() {
                          _showInfoBar = val;
                        });
                      },
                      activeColor: Theme.of(context).colorScheme.primary,
                      inactiveThumbColor: Theme.of(context)
                          .colorScheme
                          .onSurface
                          .withOpacity(0.3),
                      inactiveTrackColor:
                          Theme.of(context).colorScheme.surfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            // Carte occupe tout l'espace, infos en overlay en bas
            Expanded(
              child: Stack(
                children: [
                  // Carte
                  Positioned.fill(
                    child: Container(
                      color: Theme.of(context).colorScheme.surface,
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
                                if (_optimizedPath != null &&
                                    _optimizedPath!.isNotEmpty) {
                                  svg =
                                      _createSvgWithPath(svg, _optimizedPath!);
                                }
                                return svg;
                              },
                              backgroundColor:
                                  Theme.of(context).colorScheme.surfaceVariant,
                              overlayBuilder: (svgToScreen) {
                                final zoom = 1.0;
                                List<Widget> overlays = [];
                                if (_optimizedPath != null &&
                                    _optimizedPath!.length > 1) {
                                  final pathPoints = _optimizedPath!
                                      .map((pt) => svgToScreen(pt[0], pt[1]))
                                      .toList();
                                  overlays.add(
                                    Positioned.fill(
                                      child: IgnorePointer(
                                        ignoring: true,
                                        child: CustomPaint(
                                          painter: PathOverlayPainter(
                                              points: pathPoints, zoom: zoom),
                                        ),
                                      ),
                                    ),
                                  );
                                }
                                overlays.addAll(_pins.map((pin) {
                                  final screenPos = svgToScreen(pin.x, pin.y);
                                  return Positioned(
                                    left: screenPos.dx - 9,
                                    top: screenPos.dy - 9,
                                    child: GestureDetector(
                                      behavior: HitTestBehavior.translucent,
                                      onTap: () {
                                        setState(() {
                                          if (pin is ProductPin) {
                                            _selectedProductPin = pin;
                                            _selectedPinScreenPos = screenPos;
                                          } else {
                                            _selectedProductPin = null;
                                            _selectedPinScreenPos = null;
                                          }
                                        });
                                      },
                                      child: buildPin(pin, context),
                                    ),
                                  );
                                }));
                                // Overlay for selected ProductPin
                                if (_selectedProductPin != null &&
                                    _selectedPinScreenPos != null) {
                                  overlays.add(
                                    Positioned(
                                      left: _selectedPinScreenPos!.dx,
                                      top: _selectedPinScreenPos!.dy - 90,
                                      child: BubblePinProductInfo(
                                          productPin: _selectedProductPin!),
                                    ),
                                  );
                                }
                                // Dismiss overlay on outside tap (except navigation)
                                overlays = [
                                  GestureDetector(
                                    behavior: HitTestBehavior.translucent,
                                    onTap: () {
                                      if (_selectedProductPin != null) {
                                        setState(() {
                                          _selectedProductPin = null;
                                          _selectedPinScreenPos = null;
                                        });
                                      }
                                    },
                                    child: Stack(children: overlays),
                                  ),
                                ];
                                // The overlay Stack itself is not wrapped in IgnorePointer
                                return Stack(children: overlays);
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
                                                  .onErrorContainer),
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
                                  child: Text(_error!,
                                      textAlign: TextAlign.center),
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  // Section infos overlay en bas
                  if (_showInfoBar)
                    Align(
                      alignment: Alignment.bottomCenter,
                      child: Padding(
                        padding: const EdgeInsets.only(
                            bottom: 18.0, left: 18.0, right: 18.0),
                        child: Container(
                          decoration: BoxDecoration(
                            color: Theme.of(context)
                                .colorScheme
                                .surfaceVariant
                                .withOpacity(0.95),
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.04),
                                blurRadius: 8,
                                offset: const Offset(0, 2),
                              ),
                            ],
                          ),
                          padding: const EdgeInsets.symmetric(
                              vertical: 8, horizontal: 12),
                          child: FutureBuilder<(int, int)>(
                            future:
                                ShoppingListsRepository.fetchProductCounts(),
                            builder: (context, snapshotCounts) {
                              return FutureBuilder<(double, double)>(
                                future:
                                    ShoppingListsRepository.fetchMapPrices(),
                                builder: (context, snapshotPrices) {
                                  final counts = snapshotCounts.data;
                                  final prices = snapshotPrices.data;
                                  final availableCount = counts?.$2 ?? 0;
                                  final totalCount = counts?.$1 ?? 0;
                                  final availablePrice = prices?.$2 ?? 0.0;
                                  final distance = _optimizedPath != null &&
                                          _optimizedPath!.isNotEmpty &&
                                          _error == null
                                      ? _totalDistance
                                      : 0.0;
                                  const walkSpeed = 1.2;
                                  final shoppingTime = distance > 0
                                      ? (distance / walkSpeed)
                                      : 0.0;

                                  final width =
                                      MediaQuery.of(context).size.width;
                                  final isSmall = width < 400;
                                  final labelStyle = Theme.of(context)
                                      .textTheme
                                      .labelMedium
                                      ?.copyWith(fontSize: isSmall ? 12 : null);
                                  final valueStyle = Theme.of(context)
                                      .textTheme
                                      .titleMedium
                                      ?.copyWith(
                                          fontWeight: FontWeight.bold,
                                          fontSize: isSmall ? 14 : null);

                                  return Row(
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceEvenly,
                                    children: [
                                      _IndicatorItem(
                                        icon: Icons.shopping_cart,
                                        label: 'Produits',
                                        value: '$availableCount / $totalCount',
                                        color: Colors.blue,
                                        labelStyle: labelStyle?.copyWith(
                                            color: Colors.blue),
                                        valueStyle: valueStyle,
                                      ),
                                      _IndicatorItem(
                                        icon: Icons.euro,
                                        label: 'Prix',
                                        value:
                                            '${availablePrice.toStringAsFixed(2)}€',
                                        color: Colors.green,
                                        labelStyle: labelStyle?.copyWith(
                                            color: Colors.green),
                                        valueStyle: valueStyle,
                                      ),
                                      _IndicatorItem(
                                        icon: Icons.timer,
                                        label: 'Temps',
                                        value: shoppingTime > 0
                                            ? '${shoppingTime ~/ 60}min ${(shoppingTime % 60).toStringAsFixed(0)}s'
                                            : '--',
                                        color: Colors.deepPurple,
                                        labelStyle: labelStyle?.copyWith(
                                            color: Colors.deepPurple),
                                        valueStyle: valueStyle,
                                      ),
                                    ],
                                  );
                                },
                              );
                            },
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Widget d'indicateur moderne
class _IndicatorItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;
  final TextStyle? labelStyle;
  final TextStyle? valueStyle;
  const _IndicatorItem({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
    this.labelStyle,
    this.valueStyle,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        CircleAvatar(
          backgroundColor: color.withOpacity(0.15),
          child: Icon(icon, color: color, size: 22),
        ),
        const SizedBox(height: 6),
        Text(label,
            style: labelStyle ??
                Theme.of(context)
                    .textTheme
                    .labelMedium
                    ?.copyWith(color: color)),
        Text(value,
            style: valueStyle ??
                Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold)),
      ],
    );
  }
}
