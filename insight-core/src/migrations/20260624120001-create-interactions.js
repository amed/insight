'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('interactions', {
      id: { type: Sequelize.INTEGER, primaryKey: true, autoIncrement: true },
      interaction_id: { type: Sequelize.TEXT, allowNull: false, unique: true },
      source_filename: { type: Sequelize.TEXT, allowNull: true },
      created_at: {
        type: Sequelize.DATE,
        allowNull: false,
        defaultValue: Sequelize.fn('NOW'),
      },
    });
  },

  async down(queryInterface) {
    await queryInterface.dropTable('interactions');
  },
};
