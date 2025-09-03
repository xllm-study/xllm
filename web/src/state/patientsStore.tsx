import { create } from "zustand";
import { createJSONStorage, devtools, persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import {
  Patient,
  VariableDefinitions,
  VariableType,
  VariableValue,
} from "../../shared/types";

export interface PatientsState {
  patientValues: {
    [mrn: string]: {
      findings: {
        [varId: string]: {
          value: VariableValue;
          correctedValue?: VariableValue;
          accepted: boolean;
        };
      };
    };
  };
  init: (patients: Patient[]) => void;
  setCorrectedValue: (mrn: string, varID: string, value: VariableValue) => void;
  acceptValue: (mrn: string, varID: string) => void;
  resetValue: (mrn: string, varID: string) => void;
  resetState: () => void;
}

export const initialPatientState: PatientsState = {
  patientValues: {},
  init: () => { },
  setCorrectedValue: () => { },
  acceptValue: () => { },
  resetValue: () => { },
  resetState: () => { },
};

export const usePatientsState = create<PatientsState>()(
  persist(
    devtools(
      immer((set) => ({
        ...initialPatientState,
        init: (patients) => {
          let p: {
            [mrn: string]: {
              findings: {
                [varID: string]: {
                  value: Exclude<VariableValue, null>;
                  accepted: boolean;
                };
              };
            };
          } = {};
          for (const patient of patients) {
            const findings = patient.findings.map((finding) => [
              finding.varId,
              {
                value: finding.value!,
                accepted: false,
              },
            ]);
            p[patient.mrn] = {
              findings: Object.fromEntries(findings),
            };
          }
          set(() => ({
            patientValues: p,
          }));
        },
        setCorrectedValue: (mrn, varID, value) =>
          set((state) => {
            state.patientValues[mrn].findings[varID].correctedValue = value;
          }),
        acceptValue: (mrn, varID) =>
          set((state) => {
            state.patientValues[mrn].findings[varID].accepted = true;
          }),
        resetValue: (mrn, varID) =>
          set((state) => {
            state.patientValues[mrn].findings[varID].correctedValue = undefined;
            state.patientValues[mrn].findings[varID].accepted = false;
          }),
        resetState: () => {
          set((state) => {
            state.patientValues = {};
          }, true, {
            type: "reset",
          });
        },
      })),
    ),
    {
      name: "patient-storage", // name of the item in the storage (must be unique)
      storage: createJSONStorage(() => localStorage), // (optional) by default, 'localStorage' is used
      // storage: createJSONStorage(() => ), // (optional) by default, 'localStorage' is used
    },
  ),
);

// Helper function to format a value based on its type
const formatValue = (value: any, type: VariableType): string => {
  if (value === null || value === undefined) {
    return "";
  }

  switch (type.type) {
    case "string":
      // Escape quotes and wrap in quotes if contains comma, newline, or quote
      const stringValue = String(value);
      if (
        stringValue.includes(",") ||
        stringValue.includes("\n") ||
        stringValue.includes('"')
      ) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }
      return stringValue;

    case "bool":
      return value ? "true" : "false";

    case "enum":
      return String(value);

    case "list":
      // For lists, join array values with semicolon
      if (Array.isArray(value)) {
        return value.map((v) => formatValue(v, type.value)).join(";");
      }
      return String(value);

    case "object":
      const jsonString = JSON.stringify(value);
      return `"${jsonString.replace(/"/g, '""')}"`;
    default:
      return String(value);
  }
};

export const exportToJSON = (patientsState: PatientsState): string => {
  const export_data = Object.entries(patientsState.patientValues).map((p) => {
    const mrn = p[0];

    const findings = Object.entries(p[1].findings).map((f) => {
      const varId = f[0];
      const finding =
        f[1].correctedValue !== undefined ? f[1].correctedValue : f[1].value;

      return {
        varId,
        value: finding,
      };
    });

    return {
      mrn,
      findings,
    };
  });

  return JSON.stringify(export_data, null, 2);
};

export const exportToCSV = (
  patientsState: PatientsState,
  variableDefinitions: VariableDefinitions,
): string => {
  const variableIds = Object.keys(variableDefinitions);

  // Create header row
  const headers = [
    "MRN",
    ...variableIds.map((id) => variableDefinitions[id].name),
  ];

  // Create data rows
  const rows: string[] = [];

  // Add header row
  rows.push(headers.join(","));

  // Add patient data rows
  Object.entries(patientsState.patientValues).forEach(([mrn, patientData]) => {
    const row: string[] = [mrn];

    // For each variable, get the value (corrected value takes precedence over original value)
    variableIds.forEach((varId) => {
      const finding = patientData.findings[varId];
      const variableType = variableDefinitions[varId].type;

      if (finding) {
        // Use corrected value if it exists, otherwise use original value
        const valueToUse =
          finding.correctedValue !== undefined
            ? finding.correctedValue
            : finding.value;

        row.push(formatValue(valueToUse, variableType));
      } else {
        // No finding for this variable
        row.push("");
      }
    });

    rows.push(row.join(","));
  });

  return rows.join("\n");
};

// Utility function to download the CSV
export const downloadCSV = (
  csvContent: string,
  filename: string = "patients_export.csv",
) => {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

export const downloadJSON = (
  jsonContent: string,
  filename: string = "patients_export.json",
) => {
  const blob = new Blob([jsonContent], {
    type: "application/json;charset=utf-8;",
  });
  const link = document.createElement("a");
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};
