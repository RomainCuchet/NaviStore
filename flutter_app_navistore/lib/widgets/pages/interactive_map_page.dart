import 'package:flutter/material.dart';
import '../../services/layout_api_service.dart';
import '../../models/layout_model.dart';
import '../common/interactive_map.dart';

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
                        // 👉 Tu ajouteras ta logique ici (rafraîchir depuis l'API, recharger Hive, etc.)
                        debugPrint(
                            "TODO: Implémenter la fonction de rafraîchissement");
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
                        InteractiveMap(
                          loadSvg: () async {
                            // Essaie d'abord Hive (LayoutModel)
                            final fromHive = await LayoutModel.getFromHive();
                            if (fromHive != null &&
                                fromHive.layoutSvg.isNotEmpty) {
                              return fromHive.layoutSvg;
                            }

                            return ''; // Rien trouvé
                          },
                          backgroundColor:
                              Theme.of(context).colorScheme.surfaceVariant,
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
