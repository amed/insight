const { Model, DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  class Interaction extends Model {}

  Interaction.init(
    {
      interactionId: { type: DataTypes.TEXT, allowNull: false, unique: true },
      sourceFilename: { type: DataTypes.TEXT, allowNull: true },
    },
    {
      sequelize,
      modelName: 'Interaction',
      tableName: 'interactions',
      underscored: true,
      updatedAt: false,
    }
  );

  return Interaction;
};
