// Catch errors from async handlers and pass them to the error middleware.
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
