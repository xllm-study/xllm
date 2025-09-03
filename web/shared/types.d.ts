export type VariableType =
  | {
    type: "string";
  }
  | {
    type: "bool";
  }
  | {
    type: "enum";
    values: string[];
  }
  | {
    type: "list";
    value: VariableType;
  }
  | {
    type: "object";
    values: {
      name: string;
      value: VariableType;
    }[];
  };

export interface Note {
  id: string;
  mrn: number;
  text: string;
  date: string;
}

export type VariableValue =
  | null
  | string
  | boolean
  | string[]
  | { [key: string]: VariableValue }
  | { [key: string]: VariableValue }[];

export interface Finding {
  /** this is the name of a finding, e.g. smoking history, appendectomy, etc. */
  varId: string;
  type: "string" | "date" | "number";
  /** Value is the data predicted for this finding, e.g. for smoking history the value could be 'never smoker' */
  value: VariableValue;
  redcap_name: string;
  confidence: number;
  evidence: Evidence[];
}

export interface Patient {
  mrn: number;
  dateOfBirth?: string;
  lastName?: string;
  firstName?: string;
  gender?: string;
  findings: Finding[];
}

export interface VariableDefinition {
  name: string;
  description: string;
  type: VariableType;
  redcap_id?: string;
}

export interface VariableDefinitions {
  [varId: string]: VariableDefinition;
}
