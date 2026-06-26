const { Sequelize } = require('sequelize');
const config = require('../config');

const sequelize = new Sequelize(config.databaseUrl, {
  dialect: 'postgres',
  logging: false,
});

const Interaction = require('./interaction')(sequelize);
const Line = require('./line')(sequelize);
const InsightRecord = require('./insightRecord')(sequelize);
const RecordField = require('./recordField')(sequelize);
const FieldCitation = require('./fieldCitation')(sequelize);
const Step = require('./step')(sequelize);

// Associations
Interaction.hasMany(Line, { foreignKey: 'interactionId', as: 'lines', onDelete: 'CASCADE' });
Line.belongsTo(Interaction, { foreignKey: 'interactionId' });

Interaction.hasOne(InsightRecord, { foreignKey: 'interactionId', as: 'record', onDelete: 'CASCADE' });
InsightRecord.belongsTo(Interaction, { foreignKey: 'interactionId' });

InsightRecord.hasMany(RecordField, { foreignKey: 'recordId', as: 'fields', onDelete: 'CASCADE' });
RecordField.belongsTo(InsightRecord, { foreignKey: 'recordId' });

RecordField.hasMany(FieldCitation, { foreignKey: 'fieldId', as: 'citations', onDelete: 'CASCADE' });
FieldCitation.belongsTo(RecordField, { foreignKey: 'fieldId' });

FieldCitation.belongsTo(Line, { foreignKey: 'lineId', as: 'line' });

Interaction.hasMany(Step, { foreignKey: 'interactionId', as: 'steps', onDelete: 'CASCADE' });
Step.belongsTo(Interaction, { foreignKey: 'interactionId' });

module.exports = {
  sequelize,
  Interaction,
  Line,
  InsightRecord,
  RecordField,
  FieldCitation,
  Step,
};
