import { sql } from "drizzle-orm";
import { int, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const usersTable = sqliteTable("users_table", {
  id: text({}).primaryKey(),
});

export const EVENTS = [
  "start_session",
  "end_session",
  "start_patient",
  "finish_patient",
  "accept_patient_value",
  "pause_session",
  "resume_session",
] as const;

export type EventType = (typeof EVENTS)[number];

export const eventsTable = sqliteTable("events_table", {
  id: int().primaryKey({ autoIncrement: true }),
  timestamp: text().default(sql`(CURRENT_TIMESTAMP)`),
  userId: text().notNull(),
  type: text({
    enum: EVENTS,
  }).notNull(),
  meta: text({
    mode: "json",
  }),
});
