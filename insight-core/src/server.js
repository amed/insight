const app = require('./app');
const config = require('./config');
const { sequelize } = require('./models');

async function start() {
  await sequelize.authenticate();
  app.listen(config.port, () => {
    console.log(`insight-core listening on :${config.port}`);
  });
}

start().catch((err) => {
  console.error('failed to start insight-core', err);
  process.exit(1);
});
