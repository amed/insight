import { promises as fs } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import type { AppConfig } from "../config.js";

export class FileStorageService {
  readonly baseDir = "/data";
  readonly uploadDir = path.join(this.baseDir, "uploads");
  readonly resultDir = path.join(this.baseDir, "results");
  readonly jobsDir = path.join(this.baseDir, "jobs");

  constructor(private readonly config: AppConfig) {}

  async ensureDirs(): Promise<void> {
    await Promise.all([
      fs.mkdir(this.uploadDir, { recursive: true }),
      fs.mkdir(this.resultDir, { recursive: true }),
      fs.mkdir(this.jobsDir, { recursive: true })
    ]);
  }

  getUploadPath(originalName: string): string {
    return path.join(this.uploadDir, `${randomUUID()}${path.extname(originalName) || ""}`);
  }

  getResultPath(jobId: string, format: string): string {
    return path.join(this.resultDir, `${jobId}.${format}`);
  }

  getJobPath(jobId: string): string {
    return path.join(this.jobsDir, `${jobId}.json`);
  }

  async cleanupAgedFiles(now = Date.now()): Promise<void> {
    const ttlMs = this.config.TEMP_FILE_TTL_HOURS * 3600 * 1000;
    const files = await fs.readdir(this.uploadDir).catch(() => []);
    await Promise.all(
      files.map(async (file) => {
        const p = path.join(this.uploadDir, file);
        const stat = await fs.stat(p).catch(() => null);
        if (stat && now - stat.mtimeMs > ttlMs) {
          await fs.unlink(p).catch(() => undefined);
        }
      })
    );
  }
}
