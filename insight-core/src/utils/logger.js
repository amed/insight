const config = require('../config');

// a minimal leveled logger. the threshold is set by LOG_LEVEL (default info); anything
// noisier than the threshold is dropped. an optional meta object is printed alongside.
const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const threshold = LEVELS[config.logLevel] ?? LEVELS.info;

function emit(level, message, meta) {
  if (LEVELS[level] > threshold) return;
  const line = `${new Date().toISOString()} ${level.toUpperCase()} ${message}`;
  const out = level === 'error' ? console.error : console.log;
  if (meta === undefined) {
    out(line);
  } else {
    out(line, meta);
  }
}

module.exports = {
  error: (message, meta) => emit('error', message, meta),
  warn: (message, meta) => emit('warn', message, meta),
  info: (message, meta) => emit('info', message, meta),
  debug: (message, meta) => emit('debug', message, meta),
};
