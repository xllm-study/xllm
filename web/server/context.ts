import { CreateExpressContextOptions } from "@trpc/server/adapters/express";

export const createContext = ({ req, res }: CreateExpressContextOptions) => {
  const sessionIdCookie = req.cookies?.session || null;

  const sessionId =
    typeof sessionIdCookie === "string" && sessionIdCookie != "DELETED"
      ? sessionIdCookie
      : null;

  return {
    req,
    res,
    sessionId,
  };
};

export type Context = Awaited<ReturnType<typeof createContext>>;
