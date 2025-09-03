import { Note, Patient, VariableDefinitions } from "../shared/types";
import { readFile } from "fs/promises";
import path from "path";
import { CONFIG } from "./config";
import { z } from "zod";

const ParticipantConfigSchema = z.record(
  z.string(),
  z.object({
    mrns: z.array(z.number()),
    dataEntryMode: z.boolean().optional(),
  }),
);

// Paths
const data_path = CONFIG.DATA_PATH;
const patientsPath = path.resolve(data_path, "patients.json");
const notesPath = path.resolve(data_path, "notes.json");
const variableDefsPath = path.resolve(data_path, "variable_definitions.json");
const participantConfigPath = path.resolve(
  data_path,
  "participant_config.json",
);

// This will be filled on module load
let patients: Patient[] = [];
let notes: Note[] = [];
let variableDefs: VariableDefinitions = {};
let participantConfig: z.infer<typeof ParticipantConfigSchema> = {};

// Load all files and process on module load
async function loadAll() {
  // Read files in parallel
  const [patientsRaw, notesRaw, variableDefsRaw, participantConfigRaw] =
    await Promise.all([
      readFile(patientsPath, "utf-8"),
      readFile(notesPath, "utf-8"),
      readFile(variableDefsPath, "utf-8"),
      readFile(participantConfigPath, "utf-8"),
    ]);

  patients = JSON.parse(patientsRaw);
  notes = JSON.parse(notesRaw);
  variableDefs = JSON.parse(variableDefsRaw);
  participantConfig = ParticipantConfigSchema.parse(
    JSON.parse(participantConfigRaw),
  );
}

// Immediately load data when this module is loaded
const loadPromise = loadAll();

// Export a promise that resolves when loading is done
export const dataReady = loadPromise;

export const dataForParticipant = async (participantID: string) => {
  await dataReady;
  const mrns = participantConfig[participantID]?.mrns;
  const dataEntryMode = participantConfig[participantID]?.dataEntryMode;

  if (!mrns) {
    console.log(`No MRNs found for participant ID: ${participantID}`);
    return {
      patients,
      notes,
      variableDefs,
      dataEntryMode: false,
    };
  }

  let filteredPatients = patients.filter((p) => mrns.includes(p.mrn));

  if (dataEntryMode) {
    filteredPatients = filteredPatients.map((p) => {
      return {
        ...p,
        findings: p.findings.map((f) => ({
          ...f,
          value: null,
          evidence: [],
        })),
      };
    });
  }

  const filteredNotes = dataEntryMode
    ? []
    : notes.filter((n) => mrns.includes(n.mrn));

  return {
    patients: filteredPatients,
    notes: filteredNotes,
    variableDefs,
    dataEntryMode: dataEntryMode || false,
  };
};

// Export values (will be filled after dataReady resolves)
export { patients, notes, variableDefs, participantConfig };
