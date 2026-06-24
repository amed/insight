import { Router } from "express";
import { asyncHandler } from "../utils/async-handler.js";
import type { WhisperClient } from "../services/whisper-client.js";

export function createHealthRoutes(whisperClient: WhisperClient): Router {
  const router = Router();
  router.get(
    "/health",
    asyncHandler(async (_req, res) => {
      try {
        await whisperClient.health();
        res.json({ status: "ok", whisper: "reachable" });
      } catch {
        res.status(503).json({ status: "degraded", whisper: "unreachable" });
      }
    })
  );
  return router;
}
