import type {
  Note,
  Patient,
  VariableDefinition,
  VariableDefinitions,
  VariableType,
  VariableValue,
} from "../../shared/types";

export interface Evidence {
  confidence: number;
  value: VariableValue;
  source_note_id: string;
  source_note: Note;
  citation?: string;
}

export const evidenceValueToString = (v: VariableValue): string => {
  if (v === null) return "Unknown";
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "string") return v;
  return String(v);
};

export const loadPatients = (
  patients: Patient[],
  variable_defs: VariableDefinitions,
  notes: Note[],
  dataEntryMode: boolean = false,
) => {
  const transformedPatients: Patient[] = patients.map((p) => {
    const findings = p.findings.map((f) => {
      const type = variable_defs[f.varId]?.type;
      if (!type)
        console.log("var_id", f.varId)



      const isObjectList = type.type === "list" && type.value.type === "object";
      let value = f.value;
      if (isObjectList && f.value) {
        console.log("f.value", f.value, type, f.varId);
      }

      const evidence: Evidence[] = f.evidence.map<Evidence>((e) => ({
        ...e,
        source_note: notes.find((n) => n.id === e.source_note_id),
      }));

      return {
        ...f,
        value,
        evidence,
      };
    });

    const JANNES_MODE = import.meta.env.VITE_SHOW_ALL_VARS === "true";
    // const JANNES_MODE = false;

    return {
      ...p,
      findings: findings.filter((f) => dataEntryMode || f.evidence.length > 0 || JANNES_MODE), // filter out findings with no evidence
    };
  });
  return transformedPatients;
};

// export const getPatients = () => processedPatients as any as Patient[];

// export const getVariableDefinitions = (): {
//   [id: string]: VariableDefinition;
// } => {
//   return variable_defs as any;
// };
