const { Model, DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  class Line extends Model {}

  Line.init(
    {
      lineId: { type: DataTypes.TEXT, allowNull: false }, // stable id, e.g. "L0001"
      ordinal: { type: DataTypes.INTEGER, allowNull: false },
      speaker: { type: DataTypes.TEXT, allowNull: false },
      text: { type: DataTypes.TEXT, allowNull: false },
    },
    {
      sequelize,
      modelName: 'Line',
      tableName: 'lines',
      underscored: true,
      timestamps: false,
    }
  );

  return Line;
};
