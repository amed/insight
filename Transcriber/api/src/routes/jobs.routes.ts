import { promises as fs } from "node:fs";
import { Router } from "express";
import multer from "multer";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { transcriptionInputSchema, whisperResultSchema } from "../schemas/transcription.schemas.js";
import { ApiError } from "../middleware/error-handler.js";
import { asyncHandler } from "../utils/async-handler.js";
import type { FileStorageService } from "../services/file-storage.js";
import type { JobStore } from "../services/job-store.js";
import type { WhisperClient } from "../services/whisper-client.js";
import { asSrt, asTxt, asVtt } from "../services/transcript-formatters.js";
import type { AppConfig } from "../config.js";

const linksFor = (jobId: string) => ({
  status: `/v1/jobs/${jobId}`,
  result: `/v1/jobs/${jobId}/result`,
  download: `/v1/jobs/${jobId}/download`
});

export function createJobsRoutes(
  storage: FileStorageService,
  jobStore: JobStore,
  whisperClient: WhisperClient,
  config: AppConfig
): Router {
  const router = Router();
  const upload = multer({
    storage: multer.diskStorage({
      destination: (_req, _file, cb) => cb(null, storage.uploadDir),
      filename: (_req, file, cb) => cb(null, `${randomUUID()}${path.extname(file.originalname) || ""}`)
    }),
    limits: { fileSize: config.MAX_UPLOAD_BYTES }
  });

  router.post(
    "/v1/jobs",
    upload.single("file"),
    asyncHandler(async (req, res) => {
      if (!req.file) throw new ApiError(400, "VALIDATION_ERROR", "file is required");
      if (req.file.size <= 0) throw new ApiError(400, "VALIDATION_ERROR", "Uploaded file is empty");
      const payload = transcriptionInputSchema.parse(req.body);
      const job = await jobStore.enqueue(req.file.path, req.file.originalname, payload);
      res.status(202).json({ job_id: job.job_id, status: job.status, created_at: job.created_at, links: linksFor(job.job_id) });
    })
  );

  router.get(
    "/v1/jobs/:jobId",
    asyncHandler(async (req, res) => {
      const job = await jobStore.get(req.params.jobId);
      if (!job) throw new ApiError(404, "NOT_FOUND", "Job not found");
      res.json({
        job_id: job.job_id,
        status: job.status,
        created_at: job.created_at,
        started_at: job.started_at,
        finished_at: job.finished_at,
        error: job.error,
        output_format: job.output_format,
        links: linksFor(job.job_id)
      });
    })
  );

  router.get(
    "/v1/jobs/:jobId/result",
    asyncHandler(async (req, res) => {
      const job = await jobStore.get(req.params.jobId);
      if (!job) throw new ApiError(404, "NOT_FOUND", "Job not found");
      if (job.status === "failed") throw new ApiError(422, "JOB_FAILED", job.error ?? "Job failed");
      if (job.status !== "succeeded") throw new ApiError(422, "JOB_NOT_READY", "Job has not completed");
      if (!job.result_json_path) throw new ApiError(404, "NOT_FOUND", "Job result JSON missing");
      const raw = await fs.readFile(job.result_json_path, "utf-8");
      res.type("application/json").send(raw);
    })
  );

  router.get(
    "/v1/jobs/:jobId/download",
    asyncHandler(async (req, res) => {
      const job = await jobStore.get(req.params.jobId);
      if (!job) throw new ApiError(404, "NOT_FOUND", "Job not found");
      if (job.status === "failed") throw new ApiError(422, "JOB_FAILED", job.error ?? "Job failed");
      if (job.status !== "succeeded") throw new ApiError(422, "JOB_NOT_READY", "Job has not completed");
      const path = job.result_path ?? job.result_json_path;
      if (!path) throw new ApiError(404, "NOT_FOUND", "No downloadable result found");
      res.download(path, `${job.original_filename}.${job.output_format}`);
    })
  );

  router.delete(
    "/v1/jobs/:jobId",
    asyncHandler(async (req, res) => {
      const job = await jobStore.get(req.params.jobId);
      if (!job) throw new ApiError(404, "NOT_FOUND", "Job not found");
      await jobStore.delete(job.job_id);
      res.status(204).send();
    })
  );

  return router;
}

export async function processJob(
  jobId: string,
  jobStore: JobStore,
  whisperClient: WhisperClient,
  storage: FileStorageService
): Promise<void> {
  const job = await jobStore.get(jobId);
  if (!job) throw new Error("Job not found during processing");
  const result = whisperResultSchema.parse(
    await whisperClient.transcribe(job.upload_path, job.original_filename, {
      task: job.task,
      language: job.language,
      output_format: job.output_format,
      vad_filter: job.vad_filter,
      word_timestamps: job.word_timestamps,
      return_file: job.return_file
    })
  );
  const jsonResult = {
    id: job.job_id,
    filename: job.original_filename,
    task: result.task,
    model: result.model,
    language: result.language,
    language_probability: result.language_probability,
    duration: result.duration,
    text: result.text,
    segments: result.segments.map((segment) => ({ start: segment.start, end: segment.end, text: segment.text })),
    metadata: {
      created_at: new Date().toISOString(),
      processing_seconds: job.started_at ? (Date.now() - new Date(job.started_at).getTime()) / 1000 : 0
    }
  };
  const jsonPath = storage.getResultPath(job.job_id, "json");
  await fs.writeFile(jsonPath, JSON.stringify(jsonResult, null, 2), "utf-8");
  job.result_json_path = jsonPath;

  const content =
    job.output_format === "json"
      ? JSON.stringify(jsonResult, null, 2)
      : job.output_format === "txt"
        ? asTxt(result)
        : job.output_format === "srt"
          ? asSrt(result)
          : asVtt(result);
  const fmtPath = storage.getResultPath(job.job_id, job.output_format);
  await fs.writeFile(fmtPath, content, "utf-8");
  job.result_path = fmtPath;
  await jobStore.save(job);
}
