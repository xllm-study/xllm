import { ArrowRightIcon } from "@radix-ui/react-icons";
import confetti from "canvas-confetti";
import { useEffect } from "react";
import { useNavigate } from "react-router";
import { usePatientsState } from "../../state/patientsStore";
import { queryClient, trpc, trpcClient } from "../../utils/trpc";
import { useQueryClient } from "@tanstack/react-query";

const showConfetti = () => {
  [0, 1].forEach((x) =>
    [1, 0.7, 0.5].forEach((y) =>
      confetti({
        particleCount: 110,
        spread: 180 + Math.random() * 20,
        drift: x == 1 ? -0.2 : 0.2,
        angle: x == 1 ? 120 : 60,
        origin: { y, x },
      }),
    ),
  );
};

export const CompletePage = () => {
  useEffect(showConfetti, []);
  const navigate = useNavigate()
  // const queryClient = useQueryClient()
  // const resetState = usePatientsState((s) => s.resetState);

  // useEffect(() => {
  //   queryClient.invalidateQueries()
  //   resetState();
  // }, []);

  return (
    <div className="flex items-center justify-center h-screen w-screen">
      <div className="max-w-2xl flex flex-col gap-4">
        <p>
          <b>You did it!</b> Thanks for reviewing the assigned patients! 🎉
        </p>
        <p>
          Thank you so much for participating in this study! As a thank you,
          feel free to help yourself to some more{" "}
          <button
            className="bg-green-500 text-white rounded-md px-1 hover:bg-green-600"
            onClick={showConfetti}
          >
            confetti
          </button>
          !
        </p>


        <p>When you are ready, reset the app to continue with the second part of the study or to pass it onto the next person.


        </p>
        <button
          className="bg-black text-white rounded-md py-2 mt-8 hover:bg-gray-700 inline-flex items-center justify-center gap-1"
          onClick={() => navigate("/", { replace: true })}
        >
          Continue  <ArrowRightIcon />
        </button>
      </div>
    </div>
  );
};
