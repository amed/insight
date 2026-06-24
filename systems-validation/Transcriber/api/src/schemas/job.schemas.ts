import { z } from "zod";
import { outputFormatSchema, taskSchema } from "./transcription.schemas.js";

export const jobStatusSchema = z.enum(["queued", "processing", "succeeded", "failed"]);

export const jobRecordSchema = z.object({
  job_id: z.string().uuid(),
  status: jobStatusSchema,
  created_at: z.string(),
  started_at: z.string().nullable(),
  finished_at: z.string().nullable(),
  error: z.string().nullable(),
  original_filename: z.string(),
  upload_path: z.string(),
  result_path: z.string().nullable(),
  result_json_path: z.string().nullable(),
  task: taskSchema,
  language: z.string().optional(),
  output_format: outputFormatSchema,
  vad_filter: z.boolean(),
  word_timestamps: z.boolean(),
  return_file: z.boolean()
});

export type JobRecord = z.infer<typeof jobRecordSchema>;
