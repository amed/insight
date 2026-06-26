const { Model } = require('sequelize');

module.exports = (sequelize) => {
  class FieldCitation extends Model {}

  // Columns field_id and line_id come from the associations in models/index.js.
  FieldCitation.init(
    {},
    {
      sequelize,
      modelName: 'FieldCitation',
      tableName: 'field_citations',
      underscored: true,
      timestamps: false,
    }
  );

  return FieldCitation;
};
