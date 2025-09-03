import { eq } from "drizzle-orm";
import { z } from "zod";
import { dataForParticipant } from "./data";
import { db } from "./db";
import { eventsTable } from "./db/schema";
import { authedProcedure, publicProcedure, router } from "./trpc";

import { mkdir, writeFile } from "fs/promises";
import path from "path";
import { CONFIG } from "./config";

const eventInput = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("start_session"),
  }),
  z.object({
    type: z.literal("start_patient"),
    meta: z
      .object({
        patientId: z.string(),
      })
      .optional(),
  }),
  z.object({
    type: z.literal("accept_patient_value"),
    meta: z
      .object({
        patientId: z.string(),
        variableId: z.string(),
      })
      .optional(),
  }),
  z.object({
    type: z.literal("pause_session"),
  }),
  z.object({
    type: z.literal("resume_session"),
  }),
  z.object({
    type: z.literal("finish_patient"),
    meta: z
      .object({
        patientId: z.string(),
      })
      .optional(),
  }),
  z.object({
    type: z.literal("end_session"),
  }),
]);

export type EventInputType = z.infer<typeof eventInput>;

export const appRouter = router({
  login: publicProcedure
    .input(
      z.object({
        key: z
          .string()
          .length(7, "key not in correct format, must be 7 characters"),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      const now = new Date();
      // Set date to 1 month from now
      now.setMonth(now.getMonth() + 1);

      ctx.res.setHeader(
        "Set-Cookie",
        `session=${input.key}; HttpOnly; SameSite=Strict; Expires=${now.toUTCString()}`,
      );
      return "ok";
    }),

  userList: publicProcedure.query(async () => {
    // Retrieve users from a datasource, this is an imaginary database
    const users = [
      {
        id: 1,
      },
      {
        id: 2,
      },
    ];
    return users;
  }),
  getData: authedProcedure.query(async ({ ctx }) => {
    return await dataForParticipant(ctx.sessionId);
  }),
  me: authedProcedure.query(async ({ ctx }) => {
    return {
      sessionId: ctx.sessionId,
    };
  }),
  trackEvent: authedProcedure
    .input(eventInput)
    .mutation(async ({ ctx, input }) => {
      // @ts-ignore
      const meta = input.meta as any;
      await db
        .insert(eventsTable)
        .values({
          type: input.type,
          userId: ctx.sessionId,
          ...(meta && { meta }),
        })
        .execute();
    }),
  listEvents: authedProcedure.query(async ({ ctx }) => {
    const events = await db
      .select()
      .from(eventsTable)
      .where(eq(eventsTable.userId, ctx.sessionId));
    return events;
  }),
  storeResult: authedProcedure
    .input(z.any())
    .mutation(async ({ ctx, input }) => {
      const filePath = path.join(CONFIG.EXPORT_PATH, `${ctx.sessionId}.json`);
      console.log("Storing result in", filePath);

      try {
        // Ensure the directory existsr
        await mkdir(path.dirname(filePath), { recursive: true });

        // Write the input to the file
        await writeFile(filePath, JSON.stringify(input, null, 2), "utf8");

        return { message: "result stored successfully" };
      } catch (error) {
        console.error("Error storing result:", error);
        throw new Error("Failed to store result");
      } finally {
        ctx.res.setHeader(
          "Set-Cookie",
          `session=DELETED; HttpOnly; Secure; SameSite=Strict; Max-Age=0`,
        );
      }
    }),
});
