import { openAsBlob } from "node:fs";
import type { AppConfig } from "../config.js";
import type { TranscriptionInput, WhisperResult } from "../schemas/transcription.schemas.js";

export class WhisperClient {
  constructor(private readonly config: AppConfig) {}

  async health(): Promise<{ status: string }> {
    const res = await fetch(`${this.config.WHISPER_BASE_URL}/health`);
    if (!res.ok) throw new Error("Whisper service unavailable");
    return (await res.json()) as { status: string };
  }

  async transcribe(filePath: string, fileName: string, options: TranscriptionInput): Promise<WhisperResult> {
    const form = new FormData();
    const blob = await openAsBlob(filePath);
    form.append("file", blob, fileName);
    form.append("task", options.task ?? "transcribe");
    if (options.language) form.append("language", options.language);
    form.append("vad_filter", String(options.vad_filter ?? true));
    form.append("word_timestamps", String(options.word_timestamps ?? false));

    const controller = this.config.WHISPER_REQUEST_TIMEOUT_MS > 0 ? new AbortController() : undefined;
    const timeout = controller
      ? setTimeout(() => controller.abort(), this.config.WHISPER_REQUEST_TIMEOUT_MS)
      : undefined;
    try {
      const res = await fetch(`${this.config.WHISPER_BASE_URL}/internal/transcribe`, {
        method: "POST",
        body: form,
        signal: controller?.signal
      });
      if (!res.ok) {
        const message = await res.text();
        throw new Error(`Whisper error: ${message}`);
      }
      return (await res.json()) as WhisperResult;
    } finally {
      if (timeout) clearTimeout(timeout);
    }
  }
}
