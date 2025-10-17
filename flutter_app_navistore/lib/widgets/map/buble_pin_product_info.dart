import 'package:flutter/material.dart';

import 'map_overlays.dart';

class BubblePinProductInfo extends StatelessWidget {
  final ProductPin productPin;
  final Offset pinScreenPos;
  final Size screenSize;
  final VoidCallback onClose;

  const BubblePinProductInfo({
    Key? key,
    required this.productPin,
    required this.pinScreenPos,
    required this.screenSize,
    required this.onClose,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Bubble size and pointer
    const double bubbleWidth = 220;
    const double bubbleHeight = 80;
    const double pointerHeight = 16;
    const double pointerWidth = 28;
    const double margin = 8;

    // Determine if bubble should be above or below the pin
    bool showAbove = pinScreenPos.dy > (bubbleHeight + pointerHeight + margin);
    // Horizontal shift to keep bubble in screen
    double left = pinScreenPos.dx - bubbleWidth / 2;
    if (left < margin) left = margin;
    if (left + bubbleWidth > screenSize.width - margin)
      left = screenSize.width - bubbleWidth - margin;
    double top = showAbove
        ? pinScreenPos.dy - bubbleHeight - pointerHeight
        : pinScreenPos.dy + pointerHeight;
    if (top < margin) top = margin;
    if (top + bubbleHeight > screenSize.height - margin)
      top = screenSize.height - bubbleHeight - margin;

    // Responsive text size
    double nameFontSize = 16;
    if (productPin.name.length > 18) nameFontSize = 13;
    if (productPin.name.length > 28) nameFontSize = 11;

    return Stack(
      children: [
        Positioned(
          left: left,
          top: top,
          child: Material(
            color: Colors.transparent,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Container(
                  width: bubbleWidth,
                  height: bubbleHeight,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black26,
                        blurRadius: 12,
                        offset: Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          productPin.imagePath,
                          width: 44,
                          height: 44,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) =>
                              const Icon(Icons.broken_image, size: 36),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            FittedBox(
                              fit: BoxFit.scaleDown,
                              child: Text(
                                productPin.name,
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: nameFontSize,
                                ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${productPin.price.toStringAsFixed(2)} €',
                              style: const TextStyle(
                                color: Colors.green,
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                      // Close button
                      Padding(
                        padding: const EdgeInsets.only(left: 6.0),
                        child: GestureDetector(
                          onTap: onClose,
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.grey.shade200,
                              shape: BoxShape.circle,
                            ),
                            padding: const EdgeInsets.all(4),
                            child: const Icon(Icons.close,
                                size: 18, color: Colors.black54),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                // Pointer
                Positioned(
                  left: (bubbleWidth - pointerWidth) / 2,
                  top: showAbove ? bubbleHeight : -pointerHeight,
                  child: Transform.rotate(
                    angle: showAbove ? 3.1416 : 0,
                    child: CustomPaint(
                      size: const Size(pointerWidth, pointerHeight),
                      painter: _BubblePointerPainter(color: productPin.color),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _BubblePointerPainter extends CustomPainter {
  final Color color;

  _BubblePointerPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = Colors.white;
    final path = Path();
    path.moveTo(size.width / 2, 0);
    path.lineTo(0, size.height);
    path.lineTo(size.width, size.height);
    path.close();
    canvas.drawShadow(path, Colors.black12, 4, true);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
