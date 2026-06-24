const { Sequelize } = require('sequelize');
const config = require('../config');

const sequelize = new Sequelize(config.databaseUrl, {
  dialect: 'postgres',
  logging: false,
});

const Interaction = require('./interaction')(sequelize);
const Line = require('./line')(sequelize);
const InsightRecord = require('./insightRecord')(sequelize);

// Associations
Interaction.hasMany(Line, { foreignKey: 'interactionId', as: 'lines', onDelete: 'CASCADE' });
Line.belongsTo(Interaction, { foreignKey: 'interactionId' });

Interaction.hasOne(InsightRecord, { foreignKey: 'interactionId', as: 'record', onDelete: 'CASCADE' });
InsightRecord.belongsTo(Interaction, { foreignKey: 'interactionId' });

module.exports = { sequelize, Interaction, Line, InsightRecord };
