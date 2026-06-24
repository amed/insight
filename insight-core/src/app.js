const express = require('express');
const routes = require('./routes');
const errorHandler = require('./middleware/errorHandler');

const app = express();

app.use(express.json());

app.use('/', routes);

// Anything unmatched returns a JSON 404, not Express's default HTML.
app.use((_req, res) => {
  res.status(404).json({ error: 'not found' });
});

app.use(errorHandler);

module.exports = app;
