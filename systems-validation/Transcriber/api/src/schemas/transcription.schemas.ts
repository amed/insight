import { z } from "zod";

export const taskSchema = z.enum(["transcribe", "translate"]).default("transcribe");
export const outputFormatSchema = z.enum(["json", "txt", "srt", "vtt"]).default("json");

const boolFromMultipart = z.preprocess((value) => {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") return value.toLowerCase() === "true";
  return undefined;
}, z.boolean());

export const transcriptionInputSchema = z.object({
  task: taskSchema.optional(),
  language: z.string().regex(/^[a-z]{2,3}(-[A-Z]{2})?$/).optional(),
  output_format: outputFormatSchema.optional(),
  vad_filter: boolFromMultipart.optional(),
  word_timestamps: boolFromMultipart.optional(),
  return_file: boolFromMultipart.optional()
});

export const whisperResultSchema = z.object({
  model: z.string(),
  task: taskSchema,
  language: z.string(),
  language_probability: z.number(),
  duration: z.number(),
  text: z.string(),
  segments: z.array(
    z.object({
      start: z.number(),
      end: z.number(),
      text: z.string(),
      words: z
        .array(
          z.object({
            start: z.number(),
            end: z.number(),
            word: z.string()
          })
        )
        .optional()
    })
  )
});

export type TranscriptionInput = z.infer<typeof transcriptionInputSchema>;
export type WhisperResult = z.infer<typeof whisperResultSchema>;
