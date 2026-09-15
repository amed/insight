const config = require('../config');

// A minimal leveled logger.
// The threshold is read from config.logLevel, which the config does not define, so it stays at info.
// Anything noisier than the threshold is dropped.
// An optional meta object is printed alongside.
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
