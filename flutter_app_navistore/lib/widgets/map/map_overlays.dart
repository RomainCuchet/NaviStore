import 'package:flutter/material.dart';

// Painter pour le chemin optimisé avec triangles directionnels
class PathOverlayPainter extends CustomPainter {
  final List<Offset> points;
  final double zoom;
  PathOverlayPainter({required this.points, required this.zoom});

  @override
  void paint(Canvas canvas, Size size) {
    if (points.length < 2) return;
    final pathWidth = (4.0 * zoom).clamp(2.0, 16.0);
    final triangleSize = (10.0 * zoom).clamp(15.0, 25.0);
    final triangleSpacing = (60.0 * zoom).clamp(30.0, 120.0);

    final pathPaint = Paint()
      ..color = const Color(0xFF1E88E5)
      ..strokeWidth = pathWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..isAntiAlias = true;

    final trianglePaint = Paint()
      ..color = const Color(0xFF1E88E5)
      ..style = PaintingStyle.fill;

    // Dessiner la ligne du chemin
    final path = Path();
    path.moveTo(points[0].dx, points[0].dy);
    for (final pt in points.skip(1)) {
      path.lineTo(pt.dx, pt.dy);
    }
    canvas.drawPath(path, pathPaint);

    // Dessiner les triangles directionnels à intervalle régulier sur la polyline
    double totalLength = 0.0;
    List<double> segLengths = [];
    for (int i = 1; i < points.length; i++) {
      final segLen = (points[i] - points[i - 1]).distance;
      segLengths.add(segLen);
      totalLength += segLen;
    }
    // Calculer la direction de chaque segment
    List<double> directions = [];
    for (int i = 1; i < points.length; i++) {
      directions.add((points[i] - points[i - 1]).direction);
    }
    for (double d = triangleSpacing; d < totalLength; d += triangleSpacing) {
      double acc = 0.0;
      int segIdx = 0;
      while (segIdx < segLengths.length && acc + segLengths[segIdx] < d) {
        acc += segLengths[segIdx];
        segIdx++;
      }
      if (segIdx >= segLengths.length) break;
      final p0 = points[segIdx];
      final p1 = points[segIdx + 1];
      final seg = p1 - p0;
      final segLen = segLengths[segIdx];
      final t = (d - acc) / segLen;
      final pos = Offset(p0.dx + seg.dx * t, p0.dy + seg.dy * t);
      final angle = seg.direction;
      _drawTriangle(canvas, pos, angle, triangleSize, trianglePaint);
    }
    // Triangle au début
    if (directions.isNotEmpty) {
      _drawTriangle(
          canvas, points[0], directions[0], triangleSize, trianglePaint);
      _drawTriangle(
          canvas, points.last, directions.last, triangleSize, trianglePaint);
    }
  }

  void _drawTriangle(
      Canvas canvas, Offset pos, double angle, double size, Paint paint) {
    final path = Path();
    path.moveTo(0, 0);
    path.lineTo(-size / 2, -size);
    path.lineTo(size / 2, -size);
    path.close();
    canvas.save();
    canvas.translate(pos.dx, pos.dy);
    canvas.rotate(angle + 1.5708);
    canvas.drawPath(path, paint);
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant PathOverlayPainter oldDelegate) {
    return oldDelegate.points != points || oldDelegate.zoom != zoom;
  }
}

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
