import type { WhisperResult } from "../schemas/transcription.schemas.js";

const pad = (n: number, size = 2): string => String(n).padStart(size, "0");

function formatTimestamp(seconds: number, sep: "," | "."): string {
  const totalMs = Math.max(0, Math.floor(seconds * 1000));
  const h = Math.floor(totalMs / 3_600_000);
  const m = Math.floor((totalMs % 3_600_000) / 60_000);
  const s = Math.floor((totalMs % 60_000) / 1000);
  const ms = totalMs % 1000;
  return `${pad(h)}:${pad(m)}:${pad(s)}${sep}${pad(ms, 3)}`;
}

export function asTxt(result: WhisperResult): string {
  return `${result.text.trim()}\n`;
}

export function asSrt(result: WhisperResult): string {
  return result.segments
    .map((seg, i) => `${i + 1}\n${formatTimestamp(seg.start, ",")} --> ${formatTimestamp(seg.end, ",")}\n${seg.text.trim()}\n`)
    .join("\n");
}

export function asVtt(result: WhisperResult): string {
  const body = result.segments
    .map((seg) => `${formatTimestamp(seg.start, ".")} --> ${formatTimestamp(seg.end, ".")}\n${seg.text.trim()}\n`)
    .join("\n");
  return `WEBVTT\n\n${body}`;
}
