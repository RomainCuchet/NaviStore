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
    const double bubbleMaxWidth = 170;
    const double pointerHeight = 16;
    const double pointerWidth = 28;
    const double margin = 8;

    // Fixed font size, dynamic lines
    double nameFontSize = 10;
    int nameMaxLines = 2;
    if (productPin.name.length > 18) nameMaxLines = 3;
    if (productPin.name.length > 28) nameMaxLines = 4;

    // Calculate text height and include price
    double lineHeight = nameFontSize * 1.2;
    double textHeight = lineHeight * nameMaxLines;
    double priceHeight = 18; // Height for price text
    double verticalPadding = 12; // Top+bottom padding
    double bubbleHeight = textHeight + priceHeight + verticalPadding;
    double minHeight = 56;
    if (bubbleHeight < minHeight) bubbleHeight = minHeight;

    // Orientation logic: up/down/left/right
    bool showAbove = true;
    bool showLeft = false;
    bool showRight = false;
    double left = pinScreenPos.dx - bubbleMaxWidth / 2;
    double top = pinScreenPos.dy - bubbleHeight - pointerHeight;

    // Check for horizontal overflow (left/right)
    if (pinScreenPos.dx + pointerHeight + bubbleMaxWidth >
        screenSize.width - margin) {
      // Collision à droite, bulle à gauche
      showLeft = true;
      showRight = false;
      left = pinScreenPos.dx - bubbleMaxWidth - pointerHeight;
      top = pinScreenPos.dy - bubbleHeight / 2;
      if (top < margin) top = margin;
      if (top + bubbleHeight > screenSize.height - margin)
        top = screenSize.height - bubbleHeight - margin;
    } else if (pinScreenPos.dx - pointerHeight - bubbleMaxWidth < margin) {
      // Collision à gauche, bulle à droite
      showLeft = false;
      showRight = true;
      left = pinScreenPos.dx + pointerHeight;
      top = pinScreenPos.dy - bubbleHeight / 2;
      if (top < margin) top = margin;
      if (top + bubbleHeight > screenSize.height - margin)
        top = screenSize.height - bubbleHeight - margin;
    } else {
      // If no horizontal collision, check vertical (up/down)
      showAbove = pinScreenPos.dy > (bubbleHeight + pointerHeight + margin);
      top = showAbove
          ? pinScreenPos.dy - bubbleHeight - pointerHeight
          : pinScreenPos.dy + pointerHeight;
      // Clamp left to keep bubble fully visible horizontally
      if (left < margin) left = margin;
      if (left + bubbleMaxWidth > screenSize.width - margin)
        left = screenSize.width - bubbleMaxWidth - margin;
    }

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
                  constraints: BoxConstraints(
                    maxWidth: bubbleMaxWidth,
                    minWidth: bubbleMaxWidth,
                    minHeight: bubbleHeight,
                    maxHeight: bubbleHeight,
                  ),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  height: bubbleHeight,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black26,
                        blurRadius: 8,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Stack(
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(6),
                            child: Image.network(
                              productPin.imagePath,
                              width: 32,
                              height: 32,
                              fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) =>
                                  const Icon(Icons.broken_image, size: 24),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  productPin.name,
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: nameFontSize,
                                  ),
                                  maxLines: nameMaxLines,
                                  overflow: TextOverflow.ellipsis,
                                  softWrap: true,
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  '${productPin.price.toStringAsFixed(2)} €',
                                  style: const TextStyle(
                                    color: Colors.green,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      // Close button (very small, top right, no background)
                      Positioned(
                        top: 2,
                        right: 2,
                        child: GestureDetector(
                          onTap: onClose,
                          child: const Icon(Icons.close,
                              size: 13, color: Color(0x99000000)),
                        ),
                      ),
                    ],
                  ),
                ),
                // Pointer
                if (showLeft)
                  Positioned(
                    left: bubbleMaxWidth,
                    top: (bubbleHeight - pointerWidth) / 2,
                    child: Transform.rotate(
                      angle: 1.5708, // pointe vers la droite
                      child: CustomPaint(
                        size: const Size(pointerWidth, pointerHeight),
                        painter: _BubblePointerPainter(color: productPin.color),
                      ),
                    ),
                  )
                else if (showRight)
                  Positioned(
                    left: -pointerHeight,
                    top: (bubbleHeight - pointerWidth) / 2,
                    child: Transform.rotate(
                      angle: -1.5708, // pointe vers la gauche
                      child: CustomPaint(
                        size: const Size(pointerWidth, pointerHeight),
                        painter: _BubblePointerPainter(color: productPin.color),
                      ),
                    ),
                  )
                else
                  Positioned(
                    left: (bubbleMaxWidth - pointerWidth) / 2,
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
