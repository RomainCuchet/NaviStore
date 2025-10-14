import 'package:flutter/material.dart';
import 'package:namer_app/widgets/pages/interactive_map_page.dart';
import 'package:provider/provider.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:english_words/english_words.dart';

import 'services/product_api_service.dart';
import 'services/product_api_sync_service.dart';
import 'services/layout_api_service.dart';
import 'services/layout_api_sync_service.dart';

import 'widgets/pages/shopping_lists_page.dart';
import 'widgets/pages/browse_products_page.dart';

import 'models/product_model.dart';
import 'models/shopping_list_model.dart';
import 'models/layout_model.dart';
import 'models/product_categories_model.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");

  // Initialisation Hive
  await Hive.initFlutter();
  Hive.registerAdapter(ProductModelAdapter());
  Hive.registerAdapter(ShoppingListModelAdapter());
  Hive.registerAdapter(LayoutModelAdapter());
  Hive.registerAdapter(ProductCategoriesModelAdapter());

  await Hive.openBox<ShoppingListModel>('shopping_lists');
  await Hive.openBox<ProductModel>('products');
  await Hive.openBox<ProductCategoriesModel>('product_categories');

  // Create the API services
  final productApiService = ProductApiService(
    baseUrl: dotenv.env['API_URL'] ?? 'http://localhost:8000',
    apiKey: dotenv.env['API_KEY'] ?? '',
  );
  final layoutApiService = LayoutApiService(
    baseUrl: dotenv.env['API_URL'] ?? 'http://localhost:8000',
    apiKey: dotenv.env['API_KEY'] ?? '',
  );

  // Synchronize products at startup
  final productSyncService = ProductApiSyncService(productApiService);
  await productSyncService.fullResync();

  // Synchronize layout at startup
  final layoutSyncService = LayoutApiSyncService(api: layoutApiService);
  await layoutSyncService.syncLayout();

  runApp(
    MultiProvider(
      providers: [
        Provider<ProductApiService>.value(value: productApiService),
        Provider<LayoutApiService>.value(value: layoutApiService),
        ChangeNotifierProvider(create: (_) => MyAppState()),
      ],
      child: MyApp(),
    ),
  );
}

class MyAppState extends ChangeNotifier {
  var current = WordPair.random();
  var favorites = <WordPair>[];

  void getNext() {
    current = WordPair.random();
    notifyListeners();
  }

  void toggleFavorite(WordPair pair) {
    if (favorites.contains(pair)) {
      favorites.remove(pair);
    } else {
      favorites.add(pair);
    }
    notifyListeners();
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NaviStore',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color.fromARGB(255, 41, 61, 240),
        ),
      ),
      home: const MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key});

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final productService =
        Provider.of<ProductApiService>(context, listen: false);
    final layoutService = Provider.of<LayoutApiService>(context, listen: false);

    Widget page;
    switch (selectedIndex) {
      case 0:
        page = InteractiveMapPage(layoutService: layoutService);
        break;
      case 1:
        page = const ShoppingListsPage();
        break;
      case 2:
        page = BrowseProductsPage(productService: productService);
        break;
      default:
        throw UnimplementedError('No page for $selectedIndex');
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        return Scaffold(
          body: Row(
            children: [
              SafeArea(
                child: NavigationRail(
                  extended: constraints.maxWidth >= 600,
                  destinations: const [
                    NavigationRailDestination(
                        icon: Icon(Icons.map), label: Text('Map')),
                    NavigationRailDestination(
                        icon: Icon(Icons.list), label: Text('Shopping Lists')),
                    NavigationRailDestination(
                        icon: Icon(Icons.search), label: Text('Products')),
                  ],
                  selectedIndex: selectedIndex,
                  onDestinationSelected: (value) =>
                      setState(() => selectedIndex = value),
                ),
              ),
              Expanded(
                child: Container(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  child: page,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
