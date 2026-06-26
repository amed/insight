'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('record_fields', {
      id: { type: Sequelize.INTEGER, primaryKey: true, autoIncrement: true },
      record_id: {
        type: Sequelize.INTEGER,
        allowNull: false,
        references: { model: 'insight_records', key: 'id' },
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
      },
      name: { type: Sequelize.TEXT, allowNull: false },
      value: { type: Sequelize.TEXT, allowNull: false },
    });
    await queryInterface.addConstraint('record_fields', {
      fields: ['record_id', 'name'],
      type: 'unique',
      name: 'record_fields_record_name_unique',
    });

    await queryInterface.createTable('field_citations', {
      id: { type: Sequelize.INTEGER, primaryKey: true, autoIncrement: true },
      field_id: {
        type: Sequelize.INTEGER,
        allowNull: false,
        references: { model: 'record_fields', key: 'id' },
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
      },
      line_id: {
        type: Sequelize.INTEGER,
        allowNull: false,
        references: { model: 'lines', key: 'id' },
        onDelete: 'CASCADE',
        onUpdate: 'CASCADE',
      },
    });
    await queryInterface.addConstraint('field_citations', {
      fields: ['field_id', 'line_id'],
      type: 'unique',
      name: 'field_citations_field_line_unique',
    });
  },

  async down(queryInterface) {
    await queryInterface.dropTable('field_citations');
    await queryInterface.dropTable('record_fields');
  },
};
