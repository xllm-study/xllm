import { AlertDialog, Button, Flex } from "@radix-ui/themes";
import { useTrackEvent } from "../../utils/trackEvent";
import { useState } from "react";
import { PauseIcon, ResumeIcon } from "@radix-ui/react-icons";

export function PauseButton() {
  const [open, setOpen] = useState(false);

  const trackEvent = useTrackEvent();

  const handlePause = () => {
    trackEvent({ type: "pause_session" });
  };

  const handleResume = () => {
    trackEvent({ type: "resume_session" });
  };

  return (
    <AlertDialog.Root open={open} onOpenChange={setOpen}>
      <AlertDialog.Trigger>
        <Button
          className="flex py-2"
          size="2"
          variant="ghost"
          onClick={handlePause}
        >
          <PauseIcon />
          Take a break
        </Button>
      </AlertDialog.Trigger>
      <AlertDialog.Content
        maxWidth="450px"
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <AlertDialog.Title>Session is Paused</AlertDialog.Title>
        <AlertDialog.Description size="2">
          Are you ready to continue your session?
        </AlertDialog.Description>

        <Flex gap="3" mt="4" justify="end">
          <AlertDialog.Action>
            <Button variant="solid" color="green" onClick={handleResume}>
              <ResumeIcon />
              Resume Session
            </Button>
          </AlertDialog.Action>
        </Flex>
      </AlertDialog.Content>
    </AlertDialog.Root>
  );
}
