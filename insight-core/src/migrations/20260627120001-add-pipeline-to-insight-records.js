'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.addColumn('insight_records', 'pipeline', {
      type: Sequelize.TEXT,
      allowNull: false,
      defaultValue: 'p2', // p1 | p2 | p3
    });
    await queryInterface.addColumn('insight_records', 'config_version', {
      type: Sequelize.TEXT,
      allowNull: true,
    });
  },

  async down(queryInterface) {
    await queryInterface.removeColumn('insight_records', 'config_version');
    await queryInterface.removeColumn('insight_records', 'pipeline');
  },
};
