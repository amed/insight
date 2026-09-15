// Application runtime config.
require('dotenv').config();

module.exports = {
  port: process.env.PORT || 4000,
  databaseUrl: process.env.DATABASE_URL,
  nodeEnv: process.env.NODE_ENV || 'development',

  // Model service URLs.
  services: {
    whisper: process.env.WHISPER_URL,
    embeddings: process.env.EMBEDDINGS_URL,
    diarization: process.env.DIARIZATION_URL,
    baseline: process.env.BASELINE_URL,
    llmBaseUrl: process.env.LLM_BASE_URL,
  },

  llmModel: process.env.LLM_MODEL || 'llama3.1',
  topK: Number(process.env.RETRIEVAL_TOP_K || 5),

  // The first speaker is the agent unless otherwise defined (cluster to role policy).
  agentSpeaksFirst: process.env.AGENT_SPEAKS_FIRST !== 'false',
};
