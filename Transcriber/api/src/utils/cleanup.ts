import { promises as fs } from "node:fs";
import type { AppConfig } from "../config.js";
import type { FileStorageService } from "../services/file-storage.js";
import type { JobStore } from "../services/job-store.js";
import { jobRecordSchema } from "../schemas/job.schemas.js";

export async function runCleanup(storage: FileStorageService, _jobs: JobStore, config: AppConfig): Promise<void> {
  await storage.cleanupAgedFiles();
  if (!config.JOB_RETENTION_HOURS) return;
  const cutoff = Date.now() - config.JOB_RETENTION_HOURS * 3_600_000;
  const files = await fs.readdir(storage.jobsDir).catch(() => []);
  for (const file of files.filter((f) => f.endsWith(".json"))) {
    const p = storage.getJobPath(file.replace(".json", ""));
    const raw = await fs.readFile(p, "utf-8").catch(() => null);
    if (!raw) continue;
    const job = jobRecordSchema.safeParse(JSON.parse(raw));
    if (!job.success) continue;
    const finished = job.data.finished_at ? new Date(job.data.finished_at).getTime() : 0;
    if ((job.data.status === "succeeded" || job.data.status === "failed") && finished > 0 && finished < cutoff) {
      await Promise.all(
        [job.data.upload_path, job.data.result_path, job.data.result_json_path, p]
          .filter(Boolean)
          .map((item) => fs.unlink(item as string).catch(() => undefined))
      );
    }
  }
}
