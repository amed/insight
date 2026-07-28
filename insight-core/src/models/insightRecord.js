const { Model, DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  class InsightRecord extends Model {}

  InsightRecord.init(
    {
      status: { type: DataTypes.TEXT, allowNull: false, defaultValue: 'pending' },
      pipeline: { type: DataTypes.TEXT, allowNull: false, defaultValue: 'p2' }, // p1 | p2 | p3
      configVersion: { type: DataTypes.TEXT, allowNull: true },
    },
    {
      sequelize,
      modelName: 'InsightRecord',
      tableName: 'insight_records',
      underscored: true,
      updatedAt: false,
    }
  );

  return InsightRecord;
};
