import type { NextFunction, Request, Response } from "express";
import multer from "multer";
import { ZodError } from "zod";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: unknown
  ) {
    super(message);
  }
}

export function errorHandler(error: unknown, _req: Request, res: Response, _next: NextFunction): void {
  if (error instanceof ApiError) {
    res.status(error.status).json({ error: { code: error.code, message: error.message, details: error.details ?? {} } });
    return;
  }
  if (error instanceof ZodError) {
    res.status(400).json({ error: { code: "VALIDATION_ERROR", message: "Validation failed", details: error.flatten() } });
    return;
  }
  if (error instanceof multer.MulterError && error.code === "LIMIT_FILE_SIZE") {
    res.status(413).json({ error: { code: "PAYLOAD_TOO_LARGE", message: "Uploaded file exceeds MAX_UPLOAD_BYTES", details: {} } });
    return;
  }
  const message = error instanceof Error ? error.message : "Unexpected error";
  res.status(500).json({ error: { code: "INTERNAL_ERROR", message, details: {} } });
}
