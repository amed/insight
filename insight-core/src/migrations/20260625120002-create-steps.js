'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('steps', {
      id: { type: Sequelize.INTEGER, primaryKey: true, autoIncrement: true },
      interaction_id: {
        type: Sequelize.INTEGER,
        allowNull: false,
        references: { model: 'interactions', key: 'id' },
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
      },
      name: { type: Sequelize.TEXT, allowNull: false },
      status: { type: Sequelize.TEXT, allowNull: false }, // ok | error | skipped
      detail: { type: Sequelize.JSONB, allowNull: true },
      created_at: {
        type: Sequelize.DATE,
        allowNull: false,
        defaultValue: Sequelize.fn('NOW'),
      },
    });
  },

  async down(queryInterface) {
    await queryInterface.dropTable('steps');
  },
};
