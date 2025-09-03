import { useMutation } from "@tanstack/react-query";
import { trpc } from "./trpc";
import { useCallback } from "react";
import type { EventInputType } from "../../server/router";

export const useTrackEvent = () => {
  const mut = useMutation(trpc.trackEvent.mutationOptions({}));
  return useCallback((input: EventInputType) => mut.mutate(input), [mut]);
};
