// Application runtime config.
require('dotenv').config();

module.exports = {
  port: process.env.PORT || 4000,
  databaseUrl: process.env.DATABASE_URL,
  nodeEnv: process.env.NODE_ENV || 'development',

  // Model service URLs. Wired into processing later.
  services: {
    whisper: process.env.WHISPER_URL,
    embeddings: process.env.EMBEDDINGS_URL,
    llmBaseUrl: process.env.LLM_BASE_URL,
  },
};
