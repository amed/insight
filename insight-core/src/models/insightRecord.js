const { Model, DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  class InsightRecord extends Model {}

  InsightRecord.init(
    {
      status: { type: DataTypes.TEXT, allowNull: false, defaultValue: 'pending' },
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
