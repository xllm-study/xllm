import { ArrowRightIcon, LockOpen1Icon } from "@radix-ui/react-icons";
import { Button, TextField } from "@radix-ui/themes";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { XllmLogo } from "./utils/logo";
import { useTrackEvent } from "./utils/trackEvent";
import { trpc } from "./utils/trpc";

function LoginScreen() {
  const navigate = useNavigate();
  const [participantToken, setParticipantToken] = useState("");
  const loginMutation = useMutation(trpc.login.mutationOptions());
  const trackEvent = useTrackEvent();

  const currentUserQuery = useQuery(trpc.me.queryOptions());

  useEffect(() => {
    if (currentUserQuery.data?.sessionId) {
      navigate("/patient");
    }
  }, [currentUserQuery])

  const handleLogin = () => loginMutation.mutate(
    {
      key: participantToken,
    },
    {
      onSuccess: () => {
        trackEvent({ type: "start_session" });
        navigate("/patient");
      },
    },
  )

  return (
    <>
      <div
        className="flex-col gap-12"
        style={{
          height: "100vh",
          width: "100vw",
          background: "#F5F5F5",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <XllmLogo />
        <div className="flex flex-col gap-2 w-[300px]">
          <TextField.Root
            value={participantToken}
            onChange={(e) => setParticipantToken(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleLogin();
            }}
            size={"3"}
            placeholder="Participant Token"
          >
            <TextField.Slot>
              <LockOpen1Icon height="16" width="16" />
            </TextField.Slot>
          </TextField.Root>

          {loginMutation.isError && (
            <div className="text-red-500 text-sm">
              {loginMutation.error.message}
            </div>
          )}

          <Button
            size="2"
            color="green"
            disabled={participantToken.length < 7}
            onClick={handleLogin}
          >
            <ArrowRightIcon height="16" width="16" />
            Begin Study
          </Button>
        </div>
      </div>
    </>
  );
}

export default LoginScreen;
