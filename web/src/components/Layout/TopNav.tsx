import { TrackNextIcon } from "@radix-ui/react-icons";
import { Button } from "@radix-ui/themes";
import { useMutation } from "@tanstack/react-query";
import { useMemo } from "react";
import { useNavigate, useParams } from "react-router";
import { usePatientsState } from "../../state/patientsStore";
import { useTrackEvent } from "../../utils/trackEvent";
import { queryClient, trpc } from "../../utils/trpc";
import s from "./TopNav.module.scss";
import { PauseButton } from "./PauseButton";

export function TopNav() {
  const { mrn: currentMRN } = useParams();

  const patients = usePatientsState((s) => s.patientValues);
  const { mrns, positionInArr, nextMRN, currentPatient } = useMemo(() => {
    const mrns = Object.keys(patients).sort();
    const positionInArr = mrns.indexOf(currentMRN || "");
    return {
      mrns,
      positionInArr,
      nextMRN: positionInArr < mrns.length - 1 ? mrns[positionInArr + 1] : null,
      currentPatient: patients[currentMRN || ""],
    };
  }, [patients, currentMRN]);

  const findingProgress = currentPatient
    ? Object.values(currentPatient.findings).reduce(
      (acc, finding) => {
        if (finding.accepted) acc.completed += 1;
        acc.total += 1;
        return acc;
      },
      {
        total: 0,
        completed: 0,
      },
    )
    : { total: 0, completed: 0 };
  const allFindingsAccepted =
    findingProgress.completed === findingProgress.total;

  const navigate = useNavigate();
  const trackEvent = useTrackEvent();
  const submitState = useMutation(trpc.storeResult.mutationOptions());


  const handleNextPatient = () => {
    if (!allFindingsAccepted)
      return alert("You have not completed all findings for this patient.");

    trackEvent({ type: "finish_patient", meta: { patientId: currentMRN! } });

    if (nextMRN) {
      trackEvent({
        type: "start_patient",
        meta: { patientId: nextMRN },
      });
      navigate("/patient/" + nextMRN, {
        replace: true,
      });
    } else {
      submitState.mutate(usePatientsState.getState().patientValues, {
        onSuccess: () => {
          navigate("/complete", { replace: true });
          queryClient.resetQueries();
          usePatientsState.getState().resetState();
        },
      });
    }
  };

  return (
    <nav className={s.topNav}>
      {/* <div className="flex items-center gap-8"> */}

      <PauseButton />

      <span className="text-sm tabular-nums">
        Patient {positionInArr + 1}{" "}
        <span className="text-gray-500">/ {mrns.length}</span>
      </span>
      <Button
        variant={"soft"}
        disabled={!allFindingsAccepted}
        color="green"
        className="flex py-2"
        onClick={handleNextPatient}
        size={"2"}
      >
        Next <TrackNextIcon />
      </Button>
      {/* </div> */}

      {/* <div className="placeholder"></div> */}

      <div
        className={s.progressIndicator}
        style={{
          transform: `scaleX(${findingProgress.completed / findingProgress.total})`,
        }}
      ></div>
    </nav>
  );
}
