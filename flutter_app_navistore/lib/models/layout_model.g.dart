// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'layout_model.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class LayoutModelAdapter extends TypeAdapter<LayoutModel> {
  @override
  final int typeId = 2;

  @override
  LayoutModel read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return LayoutModel(
      layoutHash: fields[0] as String,
      layoutSvg: fields[1] as String,
    );
  }

  @override
  void write(BinaryWriter writer, LayoutModel obj) {
    writer
      ..writeByte(2)
      ..writeByte(0)
      ..write(obj.layoutHash)
      ..writeByte(1)
      ..write(obj.layoutSvg);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is LayoutModelAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
