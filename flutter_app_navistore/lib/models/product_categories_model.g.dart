// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'product_categories_model.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class ProductCategoriesModelAdapter
    extends TypeAdapter<ProductCategoriesModel> {
  @override
  final int typeId = 4;

  @override
  ProductCategoriesModel read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return ProductCategoriesModel(
      productCategories: (fields[0] as List).cast<String>(),
    );
  }

  @override
  void write(BinaryWriter writer, ProductCategoriesModel obj) {
    writer
      ..writeByte(1)
      ..writeByte(0)
      ..write(obj.productCategories);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ProductCategoriesModelAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
