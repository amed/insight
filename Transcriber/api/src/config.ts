import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const configSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().int().positive().default(3000),
  API_KEY: z.string().optional(),
  CORS_ORIGIN: z.string().default("*"),
  MAX_UPLOAD_BYTES: z.coerce.number().int().positive().default(5_368_709_120),
  TEMP_FILE_TTL_HOURS: z.coerce.number().int().positive().default(24),
  JOB_RETENTION_HOURS: z.coerce.number().int().positive().optional(),
  JOB_CONCURRENCY: z.coerce.number().int().positive().default(1),
  WHISPER_BASE_URL: z.string().url().default("http://whisper:8000"),
  WHISPER_REQUEST_TIMEOUT_MS: z.coerce.number().int().min(0).default(0)
});

export const config = configSchema.parse(process.env);
export type AppConfig = typeof config;
