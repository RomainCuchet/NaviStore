import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:xml/xml.dart';
import 'package:vector_math/vector_math_64.dart';

typedef SvgLoader = Future<String> Function();

class InteractiveMap extends StatefulWidget {
  final SvgLoader loadSvg;
  final Color? backgroundColor;
  final Widget Function(Offset Function(double x, double y))? overlayBuilder;

  const InteractiveMap({
    Key? key,
    required this.loadSvg,
    this.backgroundColor,
    this.overlayBuilder,
  }) : super(key: key);

  @override
  State<InteractiveMap> createState() => _InteractiveMapState();
}

class _InteractiveMapState extends State<InteractiveMap>
    with TickerProviderStateMixin {
  late final TransformationController _transformationController;
  Animation<Matrix4>? _animationReset;
  AnimationController? _animationController;
  String? _svgString;
  bool _loading = true;
  String? _error;
  double _minScale = 0.5;
  double _maxScale = 5.0;

  // Dimensions du SVG
  Size? _svgSize;
  Size? _viewportSize;

  @override
  void initState() {
    super.initState();
    _transformationController = TransformationController();
    _animationController = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 300));
    _loadSvg();
  }

  Future<void> _loadSvg() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final svg = await widget.loadSvg();
      if (!mounted) return;

      // Extraire les dimensions du SVG
      final size = _extractSvgDimensions(svg);

      setState(() {
        _svgString = svg;
        _svgSize = size;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Impossible de charger le plan: $e';
        _loading = false;
      });
    }
  }

  Size _extractSvgDimensions(String svgString) {
    try {
      final document = XmlDocument.parse(svgString);
      final svgElement = document.findAllElements('svg').first;

      // Essayer d'obtenir width et height
      final width = svgElement.getAttribute('width');
      final height = svgElement.getAttribute('height');

      if (width != null && height != null) {
        final w = double.tryParse(width.replaceAll(RegExp(r'[^0-9.]'), ''));
        final h = double.tryParse(height.replaceAll(RegExp(r'[^0-9.]'), ''));
        if (w != null && h != null) {
          return Size(w, h);
        }
      }

      // Sinon, essayer le viewBox
      final viewBox = svgElement.getAttribute('viewBox');
      if (viewBox != null) {
        final values = viewBox.split(RegExp(r'[\s,]+'));
        if (values.length == 4) {
          final w = double.tryParse(values[2]);
          final h = double.tryParse(values[3]);
          if (w != null && h != null) {
            return Size(w, h);
          }
        }
      }
    } catch (e) {
      debugPrint('Erreur extraction dimensions SVG: $e');
    }

    // Valeur par défaut si extraction échoue
    return const Size(1000, 1000);
  }

  @override
  void dispose() {
    _animationController?.dispose();
    _transformationController.dispose();
    super.dispose();
  }

  void _onDoubleTap() {
    final current = _transformationController.value;
    final double currentScale = current.getMaxScaleOnAxis();
    if (currentScale > 1.1) {
      _animateReset();
    } else {
      final Matrix4 zoomed = _calculateZoomMatrix(2.0);
      _animateTo(zoomed);
    }
  }

  Matrix4 _calculateZoomMatrix(double scale) {
    if (_viewportSize == null || _svgSize == null) return Matrix4.identity();

    // Calculer le centre du viewport
    final centerX = _viewportSize!.width / 2;
    final centerY = _viewportSize!.height / 2;

    return Matrix4.identity()
      ..translate(centerX, centerY)
      ..scale(scale)
      ..translate(-centerX, -centerY);
  }

  void _animateReset() {
    _animateTo(Matrix4.identity());
  }

  void _animateTo(Matrix4 target) {
    _animationController?.stop();
    final begin = _transformationController.value;
    _animationReset = Matrix4Tween(begin: begin, end: target).animate(
      CurvedAnimation(parent: _animationController!, curve: Curves.easeInOut),
    )..addListener(() {
        _transformationController.value = _animationReset!.value;
      });
    _animationController?.forward(from: 0);
  }

  // Fonction pour convertir les coordonnées SVG en coordonnées écran
  Offset _svgToScreen(double svgX, double svgY) {
    if (_svgSize == null || _viewportSize == null) {
      return Offset.zero;
    }

    // Calculer le ratio de scaling pour fit BoxFit.contain
    final scaleX = _viewportSize!.width / _svgSize!.width;
    final scaleY = _viewportSize!.height / _svgSize!.height;
    final scale = scaleX < scaleY ? scaleX : scaleY;

    // Position du SVG centré dans le viewport
    final svgDisplayWidth = _svgSize!.width * scale;
    final svgDisplayHeight = _svgSize!.height * scale;
    final offsetX = (_viewportSize!.width - svgDisplayWidth) / 2;
    final offsetY = (_viewportSize!.height - svgDisplayHeight) / 2;

    // Coordonnées dans le viewport
    final viewportX = offsetX + (svgX * scale);
    final viewportY = offsetY + (svgY * scale);

    // Appliquer la transformation (zoom/pan)
    final matrix = _transformationController.value;
    final transformed = matrix.transform3(Vector3(viewportX, viewportY, 0));

    return Offset(transformed.x, transformed.y);
  }

  @override
  Widget build(BuildContext context) {
    final bg =
        widget.backgroundColor ?? Theme.of(context).colorScheme.background;

    return Container(
      color: bg,
      child: Stack(
        children: [
          if (_loading)
            const Center(child: CircularProgressIndicator.adaptive())
          else if (_error != null)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(_error!, textAlign: TextAlign.center),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: _loadSvg,
                      child: const Text('Réessayer'),
                    )
                  ],
                ),
              ),
            )
          else if ((_svgString ?? '').isEmpty)
            Center(
              child: Text('Aucun plan disponible',
                  style: Theme.of(context).textTheme.bodyLarge),
            )
          else
            LayoutBuilder(
              builder: (context, constraints) {
                _viewportSize =
                    Size(constraints.maxWidth, constraints.maxHeight);

                return Stack(
                  children: [
                    // Le SVG dans l'InteractiveViewer
                    GestureDetector(
                      onDoubleTap: _onDoubleTap,
                      child: InteractiveViewer(
                        transformationController: _transformationController,
                        panEnabled: true,
                        scaleEnabled: true,
                        minScale: _minScale,
                        maxScale: _maxScale,
                        boundaryMargin: EdgeInsets.zero,
                        constrained: false,
                        child: SizedBox(
                          width: constraints.maxWidth,
                          height: constraints.maxHeight,
                          child: Center(
                            child: SvgPicture.string(
                              _svgString!,
                              fit: BoxFit.contain,
                              allowDrawingOutsideViewBox: false,
                              placeholderBuilder: (context) => const Center(
                                  child: CircularProgressIndicator.adaptive()),
                            ),
                          ),
                        ),
                      ),
                    ),

                    // Overlays synchronisés (pins, etc.)
                    if (widget.overlayBuilder != null)
                      ListenableBuilder(
                        listenable: _transformationController,
                        builder: (context, child) {
                          return widget.overlayBuilder!(_svgToScreen);
                        },
                      ),
                  ],
                );
              },
            ),
        ],
      ),
    );
  }
}
