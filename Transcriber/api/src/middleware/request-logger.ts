import pino from "pino";
import pinoHttp from "pino-http";
import { randomUUID } from "node:crypto";
import type { IncomingMessage, ServerResponse } from "node:http";

const logger = pino({ level: process.env.NODE_ENV === "production" ? "info" : "debug" });

export const requestLogger = pinoHttp.default({
  logger,
  genReqId: (req: IncomingMessage, res: ServerResponse) => {
    const existing = req.headers["x-request-id"];
    const id = typeof existing === "string" ? existing : randomUUID();
    res.setHeader("x-request-id", id);
    return id;
  }
});

export { logger };
