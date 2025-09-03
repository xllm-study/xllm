import { CopyIcon } from "@radix-ui/react-icons";
import { Code, DataList, Flex, IconButton } from "@radix-ui/themes";
import { useParams, useSearchParams } from "react-router";
import { VariableValue } from "../../../shared/types";
import { usePatientsState } from "../../state/patientsStore";
import { FindingElement } from "../Finding/Finding";
import { SearchBar } from "../SearchBar/SearchBar";
import s from "./Patient.module.scss";
import { useStaticState } from "../../state/InitialStateProvider";

export function Patient() {
  const { mrn } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const searchQuery = searchParams.get("finding") || "";
  const setSearchQuery = (query: string) => {
    setSearchParams((searchParams) => {
      searchParams.set("finding", query);
      return searchParams;
    });
  };
  const { patients } = useStaticState();
  const data = patients.find((p) => p.mrn === parseInt(mrn || ""));
  const patient = usePatientsState((s) => s.patientValues[mrn || ""]);

  const setCorrectedValue = usePatientsState((s) => s.setCorrectedValue);
  const acceptValue = usePatientsState((s) => s.acceptValue);
  const resetValue = usePatientsState((s) => s.resetValue);

  if (!data) return "patient not found";
  if (!mrn) return "MRN not found";
  if (!patient) return "Patient with MRN not found in state";

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: 26,
      }}
    >
      <div className={s.header}>
        <p className="mb-4">
          {data.firstName} {data.lastName}
        </p>

        <DataList.Root>
          <DataList.Item>
            <DataList.Label minWidth="88px">Date of Birth</DataList.Label>
            {data?.dateOfBirth && (
              <DataList.Value>
                {new Date(Date.parse(data.dateOfBirth)).toLocaleDateString()}
              </DataList.Value>
            )}
          </DataList.Item>
          <DataList.Item>
            <DataList.Label minWidth="88px">Sex</DataList.Label>
            {data?.gender && (
              <DataList.Value>{data.gender.toLowerCase()}</DataList.Value>
            )}
          </DataList.Item>
          <DataList.Item>
            <DataList.Label minWidth="88px">MRN</DataList.Label>
            <DataList.Value>
              <Flex align="center" gap="2">
                <Code variant="ghost">{mrn}</Code>
                <IconButton
                  size="1"
                  aria-label="Copy value"
                  color="gray"
                  variant="ghost"
                  onClick={() => navigator.clipboard.writeText(mrn)}
                >
                  <CopyIcon />
                </IconButton>
              </Flex>
            </DataList.Value>
          </DataList.Item>
        </DataList.Root>
      </div>
      <SearchBar query={searchQuery} setQuery={setSearchQuery} />
      <div
        style={{
          width: "100%",
        }}
      >
        {data.findings
          .filter((f) => searchQuery === "" || f.varId.includes(searchQuery))
          .map((f) => (
            <FindingElement
              key={f.varId}
              finding={f as any}
              accepted={patient.findings[f.varId].accepted}
              acceptValue={() => acceptValue(mrn, f.varId)}
              correctedValue={patient.findings[f.varId].correctedValue}
              setCorrectedValue={(val: VariableValue) =>
                setCorrectedValue(mrn, f.varId, val)
              }
              resetValue={() => resetValue(mrn, f.varId)}
            />
          ))}
      </div>
    </div>
  );
}
