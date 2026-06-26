const { Model, DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  class Step extends Model {}

  // a single processing step, its status, and its output (for debugging)
  Step.init(
    {
      name: { type: DataTypes.TEXT, allowNull: false },
      status: { type: DataTypes.TEXT, allowNull: false },
      detail: { type: DataTypes.JSONB, allowNull: true },
    },
    {
      sequelize,
      modelName: 'Step',
      tableName: 'steps',
      underscored: true,
      updatedAt: false,
    }
  );

  return Step;
};
