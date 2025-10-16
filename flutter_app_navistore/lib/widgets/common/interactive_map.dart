import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

typedef SvgLoader = Future<String> Function();

class InteractiveMap extends StatefulWidget {
  final SvgLoader loadSvg;
  final Color? backgroundColor;

  const InteractiveMap({
    Key? key,
    required this.loadSvg,
    this.backgroundColor,
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
      setState(() {
        _svgString = svg;
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

  @override
  void dispose() {
    _animationController?.dispose();
    _transformationController.dispose();
    super.dispose();
  }

  void _onDoubleTap() {
    final current = _transformationController.value;
    final double currentScale = current.getMaxScaleOnAxis();
    // Si zoomé, reset. Sinon zoom sur centre à 2x
    if (currentScale > 1.1) {
      _animateReset();
    } else {
      final Matrix4 zoomed = Matrix4.identity()..scale(2.0);
      _animateTo(zoomed);
    }
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

  void _zoomBy(double factor) {
    final Matrix4 cur = _transformationController.value;
    final double scale = cur.getMaxScaleOnAxis() * factor;
    if (scale < _minScale) return;
    if (scale > _maxScale) return;
    // scale around center
    final Matrix4 next = Matrix4.identity()
      ..translate(cur.getTranslation().x, cur.getTranslation().y)
      ..multiply(Matrix4.diagonal3Values(scale, scale, 1.0));
    _animateTo(next);
  }

  @override
  Widget build(BuildContext context) {
    // Colors modestes et modernes
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
            // InteractiveViewer gère pan / pinch
            GestureDetector(
              onDoubleTap: _onDoubleTap,
              child: InteractiveViewer(
                transformationController: _transformationController,
                panEnabled: true,
                scaleEnabled: true,
                minScale: _minScale,
                maxScale: _maxScale,
                boundaryMargin: const EdgeInsets.all(double.infinity),
                child: LayoutBuilder(builder: (context, constraints) {
                  // Pour que le SVG prenne l'espace disponible tout en gardant ratio
                  return ConstrainedBox(
                    constraints: BoxConstraints.tightFor(
                      width: constraints.maxWidth,
                      height: constraints.maxHeight,
                    ),
                    child: Center(
                      child: SingleChildScrollView(
                        physics: const NeverScrollableScrollPhysics(),
                        child: SizedBox(
                          width: constraints.maxWidth,
                          height: constraints.maxHeight,
                          child: SvgPicture.string(
                            _svgString!,
                            fit: BoxFit.contain,
                            allowDrawingOutsideViewBox: true,
                            // échelle automatique via BoxFit.contain
                            placeholderBuilder: (context) => const Center(
                                child: CircularProgressIndicator.adaptive()),
                          ),
                        ),
                      ),
                    ),
                  );
                }),
              ),
            ),

          // Controls minimalistes (zoom + / - et reset) en bas à gauche
          Positioned(
            left: 12,
            bottom: 12,
            child: Column(
              children: [
                _smallControlButton(
                  onPressed: () => _zoomBy(1.2),
                  icon: Icons.add,
                  tooltip: 'Zoomer',
                ),
                const SizedBox(height: 8),
                _smallControlButton(
                  onPressed: () => _zoomBy(1 / 1.2),
                  icon: Icons.remove,
                  tooltip: 'Dézoomer',
                ),
                const SizedBox(height: 8),
                _smallControlButton(
                  onPressed: _animateReset,
                  icon: Icons.center_focus_strong,
                  tooltip: 'Réinitialiser',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _smallControlButton(
      {required VoidCallback onPressed,
      required IconData icon,
      String? tooltip}) {
    return Material(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: Theme.of(context).colorScheme.primaryContainer,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(12),
        child: SizedBox(
          height: 44,
          width: 44,
          child: Center(
            child: Icon(icon,
                size: 20,
                color: Theme.of(context).colorScheme.onPrimaryContainer),
          ),
        ),
      ),
    );
  }
}
