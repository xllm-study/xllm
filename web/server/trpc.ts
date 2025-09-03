import { initTRPC, TRPCError } from "@trpc/server";
import { Context } from "./context";

/**
 * Initialization of tRPC backend
 * Should be done only once per backend!
 */

export const t = initTRPC.context<Context>().create();

/**
 * Export reusable router and procedure helpers
 * that can be used throughout the router
 */
export const router = t.router;
export const publicProcedure = t.procedure;
export const authedProcedure = t.procedure.use(async function isAuthed(opts) {
  const { ctx } = opts;

  if (!ctx.sessionId) {
    throw new TRPCError({ code: "UNAUTHORIZED" });
  }

  return opts.next({
    ctx: {
      // ✅ user value is known to be non-null now
      sessionId: ctx.sessionId,
    },
  });
});
