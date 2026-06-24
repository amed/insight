// Central error handler. Maps known errors to status codes.
// eslint-disable-next-line no-unused-vars
module.exports = (err, req, res, next) => {
  if (err.name === 'SequelizeUniqueConstraintError') {
    return res.status(409).json({ error: 'interaction_id already exists' });
  }

  const status = err.status || 500;
  if (status >= 500) {
    console.error(err);
  }

  res.status(status).json({ error: err.message || 'internal error' });
};
