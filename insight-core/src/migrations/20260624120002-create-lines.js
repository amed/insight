'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('lines', {
      id: { type: Sequelize.INTEGER, primaryKey: true, autoIncrement: true },
      interaction_id: {
        type: Sequelize.INTEGER,
        allowNull: false,
        references: { model: 'interactions', key: 'id' },
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
      },
      line_id: { type: Sequelize.TEXT, allowNull: false }, // "L0001"
      ordinal: { type: Sequelize.INTEGER, allowNull: false },
      speaker: { type: Sequelize.TEXT, allowNull: false },
      text: { type: Sequelize.TEXT, allowNull: false },
    });

    await queryInterface.addConstraint('lines', {
      fields: ['interaction_id', 'line_id'],
      type: 'unique',
      name: 'lines_interaction_line_unique',
    });
  },

  async down(queryInterface) {
    await queryInterface.dropTable('lines');
  },
};
