import { createServer } from "node:http";
import { createApp } from "./app.js";
import { config } from "./config.js";
import { logger } from "./middleware/request-logger.js";
import { runCleanup } from "./utils/cleanup.js";

const { app, storage, jobStore } = await createApp();
const server = createServer(app);

server.listen(config.PORT, () => {
  logger.info({ port: config.PORT }, "API started");
});

setInterval(() => {
  void runCleanup(storage, jobStore, config);
}, 60 * 60 * 1000).unref();

const shutdown = (signal: string) => {
  logger.info({ signal }, "Shutting down");
  server.close(() => process.exit(0));
};

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
