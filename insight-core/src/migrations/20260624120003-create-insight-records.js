'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('insight_records', {
      id: { type: Sequelize.INTEGER, primaryKey: true, autoIncrement: true },
      interaction_id: {
        type: Sequelize.INTEGER,
        allowNull: false,
        unique: true, // One record per interaction
        references: { model: 'interactions', key: 'id' },
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
      },
      status: { type: Sequelize.TEXT, allowNull: false, defaultValue: 'pending' },
      created_at: {
        type: Sequelize.DATE,
        allowNull: false,
        defaultValue: Sequelize.fn('NOW'),
      },
    });
  },

  async down(queryInterface) {
    await queryInterface.dropTable('insight_records');
  },
};
