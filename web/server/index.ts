import "dotenv/config";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import express from "express";
import { createContext } from "./context";
import { appRouter } from "./router";
import cookieParser from "cookie-parser";
export type AppRouter = typeof appRouter;
import path from "path";
import { CONFIG } from "./config";
import { green } from "./utils";
import { runMigrations } from "./db";

async function main() {
  await runMigrations();

  const app = express();
  app.use(cookieParser());

  app.use(
    "/trpc",
    createExpressMiddleware({
      router: appRouter,
      createContext,
    }),
  );

  if (process.env.NODE_ENV === "production") {
    // Serve static files from the React app
    app.use(express.static(path.join(__dirname, "static")));

    // The "catchall" handler: for any request that doesn't
    // match one above, send back the React app.
    app.get("{*any}", (_, res) => {
      res.sendFile(path.join(__dirname, "static", "index.html"));
    });
  }

  app.listen(CONFIG.PORT);
  console.log(green`Server is running on http://localhost:${CONFIG.PORT}`);
}

main();
