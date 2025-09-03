import { createContext, useContext, useEffect, useMemo } from "react";
import { useData } from "../utils/queries.tsx";
import { usePatientsState } from "./patientsStore.tsx";
import { Button } from "@radix-ui/themes";
import { loadPatients } from "../utils/data.ts";
import { Patient, VariableDefinitions } from "../../shared/types";
import { useNavigate, useParams } from "react-router";

// i have the patientsState, the patientmetaState, and the variableDefinitions

//  in initial state provider, i want to give a hook that
interface StaticStateData {
  patients: Patient[];
  variableDefs: VariableDefinitions;
  dataEntryMode: boolean;
}

const StaticStateContext = createContext<StaticStateData>({} as any);

export const InitialStateProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const initState = usePatientsState((s) => s.init);
  const patientValues = usePatientsState((s) => s.patientValues);

  const { data, isSuccess, error, isError } = useData();
  const hydratedPatients = useMemo(
    () =>
      data &&
      loadPatients(
        data.patients,
        data.variableDefs,
        data.notes,
        data.dataEntryMode,
      ),
    [data],
  );
  const navigate = useNavigate();
  const { mrn } = useParams();

  useEffect(() => {
    if (!data || !hydratedPatients) return;
    if (Object.keys(patientValues).length !== 0) {
      const sorted_mrns = Object.keys(patientValues).sort();

      if (!mrn) {
        navigate("/patient/" + sorted_mrns[0]);
      }
      return;
    }
    initState(hydratedPatients);
  }, [data, isSuccess, patientValues, hydratedPatients]);

  useEffect(() => {
    console.log("isError", isError, error);
    if (isError && error.message === "UNAUTHORIZED") navigate("/");
  }, [isError, error]);

  if (Object.keys(patientValues).length === 0 || !data || !hydratedPatients)
    return (
      <StaticStateContext.Provider value={{} as any}>
        <div className="flex items-center justify-center h-screen">
          <Button loading variant="ghost" />
        </div>
      </StaticStateContext.Provider>
    );

  return (
    <StaticStateContext.Provider
      value={{
        patients: hydratedPatients,
        variableDefs: data.variableDefs,
        dataEntryMode: data.dataEntryMode,
      }}
    >
      {children}
    </StaticStateContext.Provider>
  );
};

export const useStaticState = () => useContext(StaticStateContext);
