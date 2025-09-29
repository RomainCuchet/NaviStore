// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'shopping_list_model.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class ShoppingListModelAdapter extends TypeAdapter<ShoppingListModel> {
  @override
  final int typeId = 0;

  @override
  ShoppingListModel read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return ShoppingListModel(
      id: fields[0] as String,
      name: fields[1] as String,
      products: (fields[2] as List).cast<ProductModel>(),
    );
  }

  @override
  void write(BinaryWriter writer, ShoppingListModel obj) {
    writer
      ..writeByte(3)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.name)
      ..writeByte(2)
      ..write(obj.products);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ShoppingListModelAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
