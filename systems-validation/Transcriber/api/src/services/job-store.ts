import { promises as fs } from "node:fs";
import { randomUUID } from "node:crypto";
import { jobRecordSchema, type JobRecord } from "../schemas/job.schemas.js";
import type { FileStorageService } from "./file-storage.js";
import type { TranscriptionInput } from "../schemas/transcription.schemas.js";

export class JobStore {
  private queue: string[] = [];
  private processing = 0;

  constructor(
    private readonly storage: FileStorageService,
    private readonly concurrency: number,
    private readonly worker: (job: JobRecord) => Promise<void>
  ) {}

  async enqueue(uploadPath: string, originalName: string, options: TranscriptionInput): Promise<JobRecord> {
    const id = randomUUID();
    const job: JobRecord = {
      job_id: id,
      status: "queued",
      created_at: new Date().toISOString(),
      started_at: null,
      finished_at: null,
      error: null,
      original_filename: originalName,
      upload_path: uploadPath,
      result_path: null,
      result_json_path: null,
      task: options.task ?? "transcribe",
      language: options.language,
      output_format: options.output_format ?? "json",
      vad_filter: options.vad_filter ?? true,
      word_timestamps: options.word_timestamps ?? false,
      return_file: options.return_file ?? false
    };
    await this.save(job);
    this.queue.push(id);
    void this.pump();
    return job;
  }

  async get(jobId: string): Promise<JobRecord | null> {
    const p = this.storage.getJobPath(jobId);
    const raw = await fs.readFile(p, "utf-8").catch(() => null);
    if (!raw) return null;
    return jobRecordSchema.parse(JSON.parse(raw));
  }

  async delete(jobId: string): Promise<void> {
    const job = await this.get(jobId);
    if (!job) return;
    const removals = [job.upload_path, job.result_path, job.result_json_path, this.storage.getJobPath(jobId)].filter(Boolean) as string[];
    await Promise.all(removals.map((p) => fs.unlink(p).catch(() => undefined)));
  }

  async recover(): Promise<void> {
    const files = await fs.readdir(this.storage.jobsDir).catch(() => []);
    for (const file of files.filter((f) => f.endsWith(".json"))) {
      const job = await this.get(file.replace(".json", ""));
      if (!job) continue;
      if (job.status === "queued") {
        this.queue.push(job.job_id);
      } else if (job.status === "processing") {
        job.status = "failed";
        job.error = "Job interrupted during previous process lifecycle";
        job.finished_at = new Date().toISOString();
        await this.save(job);
      }
    }
    void this.pump();
  }

  async save(job: JobRecord): Promise<void> {
    await fs.writeFile(this.storage.getJobPath(job.job_id), JSON.stringify(job, null, 2), "utf-8");
  }

  private async pump(): Promise<void> {
    while (this.processing < this.concurrency && this.queue.length > 0) {
      const next = this.queue.shift();
      if (!next) return;
      this.processing += 1;
      void this.runOne(next).finally(() => {
        this.processing -= 1;
        void this.pump();
      });
    }
  }

  private async runOne(jobId: string): Promise<void> {
    const job = await this.get(jobId);
    if (!job) return;
    job.status = "processing";
    job.started_at = new Date().toISOString();
    await this.save(job);
    try {
      await this.worker(job);
      const done = (await this.get(jobId)) ?? job;
      done.status = "succeeded";
      done.finished_at = new Date().toISOString();
      await this.save(done);
    } catch (error) {
      const fail = (await this.get(jobId)) ?? job;
      fail.status = "failed";
      fail.error = error instanceof Error ? error.message : "Unknown job failure";
      fail.finished_at = new Date().toISOString();
      await this.save(fail);
    }
  }
}
