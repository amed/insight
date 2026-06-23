import { promises as fs } from "node:fs";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { Router } from "express";
import multer from "multer";
import { transcriptionInputSchema, whisperResultSchema } from "../schemas/transcription.schemas.js";
import { ApiError } from "../middleware/error-handler.js";
import { asyncHandler } from "../utils/async-handler.js";
import type { FileStorageService } from "../services/file-storage.js";
import type { WhisperClient } from "../services/whisper-client.js";
import { asSrt, asTxt, asVtt } from "../services/transcript-formatters.js";
import type { AppConfig } from "../config.js";

export function createTranscriptionsRoutes(storage: FileStorageService, whisperClient: WhisperClient, config: AppConfig): Router {
  const router = Router();
  const upload = multer({
    storage: multer.diskStorage({
      destination: (_req, _file, cb) => cb(null, storage.uploadDir),
      filename: (_req, file, cb) => cb(null, `${randomUUID()}${path.extname(file.originalname) || ""}`)
    }),
    limits: { fileSize: config.MAX_UPLOAD_BYTES }
  });

  router.post(
    "/v1/transcriptions",
    upload.single("file"),
    asyncHandler(async (req, res) => {
      if (!req.file) throw new ApiError(400, "VALIDATION_ERROR", "file is required");
      if (req.file.size <= 0) throw new ApiError(400, "VALIDATION_ERROR", "Uploaded file is empty");

      const payload = transcriptionInputSchema.parse(req.body);
      const outputFormat = payload.output_format ?? "json";
      const returnFile = payload.return_file ?? false;

      const started = performance.now();
      try {
        const whisper = whisperResultSchema.parse(await whisperClient.transcribe(req.file.path, req.file.originalname, payload));
        const responseJson = {
          id: randomUUID(),
          filename: req.file.originalname,
          task: whisper.task,
          model: whisper.model,
          language: whisper.language,
          language_probability: whisper.language_probability,
          duration: whisper.duration,
          text: whisper.text,
          segments: whisper.segments.map((segment) => ({
            start: segment.start,
            end: segment.end,
            text: segment.text
          })),
          metadata: {
            created_at: new Date().toISOString(),
            processing_seconds: Number(((performance.now() - started) / 1000).toFixed(3))
          }
        };

        if (outputFormat === "json" && !returnFile) {
          res.json(responseJson);
          return;
        }

        const filePath = storage.getResultPath(responseJson.id, outputFormat);
        const content =
          outputFormat === "json"
            ? JSON.stringify(responseJson, null, 2)
            : outputFormat === "txt"
              ? asTxt(whisper)
              : outputFormat === "srt"
                ? asSrt(whisper)
                : asVtt(whisper);
        await fs.writeFile(filePath, content, "utf-8");
        res.download(filePath, `${req.file.originalname}.${outputFormat}`, async () => {
          await fs.unlink(filePath).catch(() => undefined);
        });
      } catch (error) {
        throw new ApiError(502, "WHISPER_UPSTREAM_ERROR", error instanceof Error ? error.message : "Whisper request failed");
      } finally {
        await fs.unlink(req.file.path).catch(() => undefined);
      }
    })
  );
  return router;
}
