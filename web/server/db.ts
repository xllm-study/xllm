import { drizzle } from "drizzle-orm/libsql";
import { migrate } from "drizzle-orm/libsql/migrator";
import { CONFIG } from "./config";

export const db = drizzle(CONFIG.DB_FILE_NAME);

const dirname = typeof __dirname == "string" ? __dirname : import.meta.dirname;

console.log("Using database file:", `${dirname}/drizzle`);
export const runMigrations = () =>
  migrate(db, {
    // migrationsFolder: "./drizzle",
    // use current dirname as base and then /drizzle
    migrationsFolder: `${dirname}/drizzle`,
  });
