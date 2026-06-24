import express from "express";
import cors from "cors";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import swaggerUi from "swagger-ui-express";
import { OpenAPIRegistry, OpenApiGeneratorV3 } from "@asteasolutions/zod-to-openapi";
import { config } from "./config.js";
import { requestLogger } from "./middleware/request-logger.js";
import { errorHandler, ApiError } from "./middleware/error-handler.js";
import { createHealthRoutes } from "./routes/health.routes.js";
import { createTranscriptionsRoutes } from "./routes/transcriptions.routes.js";
import { createJobsRoutes, processJob } from "./routes/jobs.routes.js";
import { FileStorageService } from "./services/file-storage.js";
import { WhisperClient } from "./services/whisper-client.js";
import { JobStore } from "./services/job-store.js";
import type { JobRecord } from "./schemas/job.schemas.js";

export async function createApp() {
  const app = express();
  const storage = new FileStorageService(config);
  await storage.ensureDirs();
  const whisperClient = new WhisperClient(config);

  let jobStore: JobStore;
  const worker = async (job: JobRecord): Promise<void> => {
    await processJob(job.job_id, jobStore, whisperClient, storage);
  };
  jobStore = new JobStore(storage, config.JOB_CONCURRENCY, worker);
  await jobStore.recover();

  app.use(requestLogger);
  app.use(helmet());
  app.use(cors({ origin: config.CORS_ORIGIN === "*" ? true : config.CORS_ORIGIN.split(",") }));
  app.use(express.json({ limit: "1mb" }));
  app.use(rateLimit({ windowMs: 60_000, limit: 120 }));

  app.use((req, _res, next) => {
    if (config.API_KEY && req.header("x-api-key") !== config.API_KEY) {
      next(new ApiError(401, "UNAUTHORIZED", "Missing or invalid API key"));
      return;
    }
    next();
  });

  app.use(createHealthRoutes(whisperClient));
  app.use(createTranscriptionsRoutes(storage, whisperClient, config));
  app.use(createJobsRoutes(storage, jobStore, whisperClient, config));

  const registry = new OpenAPIRegistry();
  const multipartSchema: any = {
    type: "object",
    required: ["file"],
    properties: {
      file: { type: "string", format: "binary" },
      task: { type: "string", enum: ["transcribe", "translate"], default: "transcribe" },
      language: { type: "string" },
      output_format: { type: "string", enum: ["json", "txt", "srt", "vtt"], default: "json" },
      vad_filter: { type: "boolean", default: true },
      word_timestamps: { type: "boolean", default: false },
      return_file: { type: "boolean", default: false }
    }
  };
  registry.registerPath({ method: "get", path: "/health", responses: { 200: { description: "Health response" } } });
  registry.registerPath({
    method: "post",
    path: "/v1/transcriptions",
    request: { body: { content: { "multipart/form-data": { schema: multipartSchema } } } },
    responses: { 200: { description: "Transcription result" } }
  });
  registry.registerPath({
    method: "post",
    path: "/v1/jobs",
    request: { body: { content: { "multipart/form-data": { schema: multipartSchema } } } },
    responses: { 202: { description: "Queued job" } }
  });
  registry.registerPath({ method: "get", path: "/v1/jobs/{jobId}", responses: { 200: { description: "Job status" } } });
  registry.registerPath({ method: "get", path: "/v1/jobs/{jobId}/result", responses: { 200: { description: "Job JSON result" } } });
  registry.registerPath({ method: "get", path: "/v1/jobs/{jobId}/download", responses: { 200: { description: "Download file" } } });
  registry.registerPath({ method: "delete", path: "/v1/jobs/{jobId}", responses: { 204: { description: "Deleted" } } });
  const generator = new OpenApiGeneratorV3(registry.definitions);
  const openapi = generator.generateDocument({
    openapi: "3.0.3",
    info: { title: "Transcription Platform API", version: "1.0.0" }
  });
  app.get("/openapi.json", (_req, res) => res.json(openapi));
  app.use("/docs", swaggerUi.serve, swaggerUi.setup(openapi));

  app.use(errorHandler);
  return { app, storage, jobStore };
}
