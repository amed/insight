'use strict';

module.exports = {
  async up(queryInterface, Sequelize) {
    // Segment times in milliseconds from the audio path.
    // Transcript uploads carry none, so both stay null there (nullable on purpose).
    await queryInterface.addColumn('lines', 'start_ms', {
      type: Sequelize.INTEGER,
      allowNull: true,
    });
    await queryInterface.addColumn('lines', 'end_ms', {
      type: Sequelize.INTEGER,
      allowNull: true,
    });
  },

  async down(queryInterface) {
    await queryInterface.removeColumn('lines', 'end_ms');
    await queryInterface.removeColumn('lines', 'start_ms');
  },
};
