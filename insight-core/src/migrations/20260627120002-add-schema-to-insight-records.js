'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    // Pre-schema records stay null and are excluded from summaries (nullable on purpose).
    await queryInterface.addColumn('insight_records', 'schema_name', {
      type: Sequelize.TEXT,
      allowNull: true,
    });
    await queryInterface.addColumn('insight_records', 'schema_version', {
      type: Sequelize.INTEGER,
      allowNull: true,
    });
    await queryInterface.addColumn('insight_records', 'schema_hash', {
      type: Sequelize.TEXT,
      allowNull: true,
    });
  },

  async down(queryInterface) {
    await queryInterface.removeColumn('insight_records', 'schema_hash');
    await queryInterface.removeColumn('insight_records', 'schema_version');
    await queryInterface.removeColumn('insight_records', 'schema_name');
  },
};
