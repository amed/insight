const { Model, DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  class RecordField extends Model {}

  RecordField.init(
    {
      name: { type: DataTypes.TEXT, allowNull: false },
      value: { type: DataTypes.TEXT, allowNull: false },
    },
    {
      sequelize,
      modelName: 'RecordField',
      tableName: 'record_fields',
      underscored: true,
      timestamps: false,
    }
  );

  return RecordField;
};
