import { useQuery } from "@tanstack/react-query";
import { trpc } from "./trpc";

export const useData = () =>
  useQuery(
    trpc.getData.queryOptions(undefined, {
      // select: transformData,
      refetchOnMount: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      staleTime: Infinity,
    }),
  );
