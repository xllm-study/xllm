# extraction.py
# > this is the main extraction pipeline of this project.
#
# ┌──────────────────┐    ┌──────────────────────┐    ┌─────────────────────────┐
# │ raw_notes.csv    ├─┬─►│ extract stage 1 vars ├─┬─►│ export to /data/web/... │
# ├──────────────────┤ │  ├──────────────────────┤ │  └─────────────────────────┘
# │ patient_meta.csv ├─┘  │ compute stage 2 vars │ │                             
# └──────────────────┘    ├──────────────────────┤ │                             
#                         │ extract stage 2 vars ├─┘                             
#                         └──────────────────────┘                               
import argparse
from enum import Enum
import json
from typing import List, Dict, Any, TypedDict, Union, Optional
from pydantic import BaseModel, TypeAdapter
import numpy as np
from openai import OpenAI
import subprocess
import requests
import time
from src.xllm import utils
from src.xllm import variables
from src.xllm.utils import Chunk, MRNChunks
import traceback
from tqdm import tqdm
from contextlib import contextmanager
import os


files = {
    "val": {
        "notes": "/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/filtered_notes_val.csv",
        "patients_meta": "/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/patient_meta.csv",
    },
    "study": {
        "notes": "/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/filtered_notes_final_cohort.csv",
        "patients_meta": "/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/patient_meta_final_cohort.csv"
    }
}

set = "study"
NOTES_FILE = files[set]["notes"]
PATIENTS_META_FILE = files[set]["patients_meta"]

def process_chunk(
    client: OpenAI, chunk: Chunk, clean_schema: Dict, response_format: Any, patient_meta: Optional[utils.PatientMeta] = None
):
    patient_meta_str = utils.get_patient_meta_prompt(patient_meta) if patient_meta is not None else ""

    completion = client.beta.chat.completions.parse(
        model="google/gemma-3-27b-it", # this does nothing when using llama.cpp, but is required
        messages=[
            {
                "role": "user",
                "content": "You're a medical professional tasked with extracting structured data from medical notes. "
                + "NEVER use newlines or \t in your output. Use the schema provided to extract the data. "
                + "If you can't find the information about one of the fields, return null. E.g. when the notes don't mention an appendectomy, don't return false, but null for the whole field. "
                # + "When adding citations to the values, only cite the fewest words possible."
                + "When adding citations to the values, only cite the relevant words."
                + "When replying with a date, ALWAYS use ISO format (YYYY-MM-DD, YYYY-MM or YYYY)."
                # + " Don't include the family members history if asked about the personal history."
                + patient_meta_str
                + f"\n<schema>{json.dumps(clean_schema)}</schema>"
                + chunk["text"],
            },
        ],
        response_format=response_format,
    )
    return completion.choices[0].message.parsed


def main(args, llm_endpoint: str):
    client = OpenAI(
        base_url=llm_endpoint,
        # api_key=os.environ.get("OPENAI_API_KEY"),
        api_key="ollama",  # required, but unused
    )

    np.random.seed(42)

    notes = utils.get_notes(NOTES_FILE)
    patients_meta = utils.get_patient_meta_dict(PATIENTS_META_FILE)

    # take mrns from patients_meta:
    all_mrns = np.array(list(patients_meta.keys()))
    # validated_mrns = {
    #     1562017,
    #     1574125,
    #     1610262,
    #     1653585,
    #     1721858,
    #     1745696,
    #     1775093,
    #     1859297,
    #     1894627,
    #     2036408,
    #     2147591,
    #     2181660,
    # }

    # all_mrns = np.array([1713222])

    # all_mrns = notes["MRN"].unique()
    all_mrns.sort()

    mrn_shards = np.array_split(all_mrns, args.total_shards)
    mrns = mrn_shards[args.shard_id]

    if len(mrns) == 0:
        print(f"Shard {args.shard_id} has no MRNs to process. Exiting.")
        return

    print(f"Processing {len(mrns)} MRNs for this shard (from a total of {len(all_mrns)}).")

    # mrns = notes["MRN"].unique()
    # mrns = np.random.choice(mrns, 3)
    # if not np.isin(1789424, mrns):
    #     mrn = np.append(mrns, 1789424)
    # mrns = np.array([3137583])
    # mrns_str = mrns.astype(str)

    notes = notes[notes["MRN"].isin(mrns)]
    chunks = utils.chunk_notes(notes, 18000)

    stage_1_vars = {
        key: value
        for key, value in variables.LM_VARIABLES.items()
        if value.is_active is None
    }
    StageOneVarCls = variables.create_medical_record_class(stage_1_vars)
    s1_clean_schema = utils.strip_titles_and_refs(TypeAdapter(StageOneVarCls).json_schema())

    class PatientRun(TypedDict):
        mrn: int
        runs: List[StageOneVarCls]

    runsByPatient: List[PatientRun] = []

    for mrnChunk in tqdm(chunks, desc="Patients Stage I", position=0):
        processed_chunks = []
        patient_meta = patients_meta.get(mrnChunk["MRN"], None)

        for chunk in tqdm(mrnChunk["chunks"], desc="Chunk n of patient", position=1):
            processed_chunk = process_chunk(client, chunk, s1_clean_schema, StageOneVarCls, patient_meta)
            processed_chunks.append(processed_chunk)

        runsByPatient.append({"mrn": mrnChunk["MRN"], "runs": processed_chunks})

    for patient in tqdm(runsByPatient, desc="Patients Stage II", position=0):
        mrn = patient["mrn"]
        # runs = patient["runs"]
        resolved_vars: Dict[str, Any] = {}

        # 1. for each variable
        for var_id, var in stage_1_vars.items():
            resolved = None
            individual_values: List[variables.MedicalFact] = [
                run.__dict__[var_id]
                for run in patient["runs"]
                if  var_id in run.__dict__ and run.__dict__[var_id] is not None
            ]
            if len(individual_values) > 0 and var.resolver is not None:
                # 2. resolve the variable from runs
                chunk_values: List[variables.ChunkValue] = []
                for v in individual_values:
                    matching_notes = notes[notes["NOTE_ID"] == v.note_id]

                    if matching_notes.empty:
                        print("Warning: No matching note found for NOTE_ID", v.note_id)
                        continue

                    chunk_values.append(
                        variables.ChunkValue(
                            date=variables.PartialDate.parse(
                                matching_notes["NOTE_DATE"].iloc[0]
                            ),
                            value=v.value,
                        )
                    )

                resolved = var.resolver(chunk_values)
            resolved_vars[var_id] = resolved

        # 3. compute activation function for all vars where is_active is not None
        stage_2_vars = {
            key: value
            for key, value in variables.LM_VARIABLES.items()
            if value.is_active is not None and value.is_active(resolved_vars)
        }

        if len(stage_2_vars) == 0:
            print(f"No active variables for MRN {mrn}. Skipping stage 2.")
            continue

        # 4. create new class with activated vars
        StageTwoVarCls = variables.create_medical_record_class(stage_2_vars)
        s2_clean_schema = utils.strip_titles_and_refs(
            TypeAdapter(StageTwoVarCls).json_schema()
        )

        # 5. for each chunk, invoke the llm again
        mrnChunk: MRNChunks = next((item for item in chunks if item["MRN"] == mrn))
        processed_chunks = []
        patient_meta = patients_meta.get(mrn, None)
        for chunk in tqdm(mrnChunk["chunks"], desc="Chunk n of patient", position=1):
            processed_chunk = process_chunk(client, chunk, s2_clean_schema, StageTwoVarCls, patient_meta)
            processed_chunks.append(processed_chunk)

        patient["runs"].extend(processed_chunks)

    class Evidence(TypedDict):
        source_note_id: int
        citation: str
        value: Union[str, int, float, bool, None]
        confidence: float

    class Finding(TypedDict):
        varId: str
        redcap_name: Optional[str]
        value: Union[str, int, float, bool, None]
        evidence: List[Evidence]
        confidence: float


    class ProcessedPatient(TypedDict):
        mrn: int
        findings: List[Finding]
        dateOfBirth: Union[str, None]  # Assuming dateOfBirth is a string in ISO format
        firstName: Union[str, None]  # Optional to allow for missing data
        lastName: Union[str, None]
        gender: Union[str, None]

    def get_value(obj):
        if obj is None:
            return None
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, "value"):
            if isinstance(obj.value, Enum):
                return obj.value.value
            else:
                return obj.value
        elif isinstance(obj, list):
            return [get_value(item) for item in obj]
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        else:
            return obj

    used_vars = {key: value for key, value in variables.LM_VARIABLES.items()}

    processed_patients: List[ProcessedPatient] = []
    for p in runsByPatient:
        patient_meta = patients_meta.get(p["mrn"], None)

        pp: ProcessedPatient = {
            "mrn": p["mrn"],
            "findings": [],
            "dateOfBirth": patient_meta.date_of_birth if  patient_meta else None,
            "firstName": patient_meta.first_name if  patient_meta else None,
            "lastName": patient_meta.last_name if  patient_meta else None,
            "gender": patient_meta.gender if  patient_meta else None,
        }
       
        for var_id, var_def in used_vars.items():
            # get a list of all the values for the variable in all runs
            run_values: List[variables.MedicalFact] = [
                run.__dict__[var_id]
                for run in p["runs"]
                if var_id in run.__dict__ and run.__dict__[var_id] is not None
            ]
            resolved_value = None
            if len(run_values) > 0 and var_def.resolver is not None:
                chunk_values = []
                for v in run_values:
                    matching_notes = notes[notes["NOTE_ID"] == v.note_id]
                    if matching_notes.empty:
                        print("Warning: No matching note found for NOTE_ID", v.note_id)
                        continue

                    chunk_values.append(
                        variables.ChunkValue(
                            date=variables.PartialDate.parse(
                                matching_notes["NOTE_DATE"].iloc[0]
                            ),
                            value=v.value,
                        )
                    )
                resolved_value = var_def.resolver(chunk_values)

            evidence = []
            for run in p["runs"]:
                if var_id in run.__dict__ and run.__dict__[var_id] is not None:
                    var_in_run = run.__dict__[var_id]

                    # v = var_in_run.value.value if isinstance(var_in_run, Enum) else var_in_run.value
                    # print(var_in_run,)
                    # if isinstance(v, variables.RelativeCancerInfo):
                    evidence.append(
                        {
                            "source_note_id": var_in_run.note_id,
                            "citation": var_in_run.citation,
                            "value": get_value(var_in_run.value),
                            "confidence": 1.0,
                        }
                    )
            # add finding to processed patient
            pp["findings"].append(
                {
                    "varId": var_id,
                    "redcap_name": var_def.redcap_id,
                    "value": get_value(resolved_value),
                    "evidence": evidence,
                    "confidence": 1.0,
                }
            )
        processed_patients.append(pp)

    output_dir = (
        f"/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/shards/{args.run_id}/"
    )

    # make sure folder exists:
    os.makedirs(output_dir, exist_ok=True)

    patients_output_filename = f"patients_shard_{args.shard_id}_of_{args.total_shards}.json"
    with open(output_dir + patients_output_filename, "w") as f:
        json.dump(processed_patients, f)
        print(f"Saved processed patients to {output_dir + patients_output_filename}")

    notes_output_filename = f"notes_shard_{args.shard_id}_of_{args.total_shards}.json"
    notes_dict = notes.rename(
        columns={
            "NOTE_ID": "id",
            "MRN": "mrn",
            "NOTE_DATE": "date",
            "NOTE_TEXT": "text",
        }
    ).to_json(orient="records")
    with open(output_dir + notes_output_filename, "w") as f:
        f.write(notes_dict)
        print(f"Saved notes for this shard to {output_dir + notes_output_filename}")

    # run metadata if shard_id == 0
    if args.shard_id == 0:
        with open(output_dir + "metadata.json", "w") as f:
            json.dump({
                "total_shards": args.total_shards,
                "shard_id": args.shard_id,
                "run_id": args.run_id,
                "notes_file": NOTES_FILE,
                "patients_meta_file": PATIENTS_META_FILE,
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            }, f)


@contextmanager
def init_server(log_file_path, shard_id: int):
    print("starting inference server...")
    port = 5912 + shard_id
    with open(log_file_path, "w") as log_file:
        server_process = subprocess.Popen(
            # ["sh", "medgemma.sh", "--port", str(port)],
            ["sh", "llama3.3.sh", "--port", str(port)], 
            stderr=log_file
        )
        try:
            # wait for the server to start
            url = f"http://localhost:{port}/health"
            start_time = time.time()
            while True:
                if time.time() - start_time > 120:  # timeout after 120 seconds
                    print("Server did not start in time. Exiting.")
                    server_process.terminate()
                    yield (None, None)
                    return
                try:
                    res = requests.get(url)
                    if res.status_code == 200:
                        print("Server is running")
                        break
                except Exception as e:
                    print(".", end="")
                time.sleep(1)
            yield (server_process, f"http://localhost:{port}/v1")
        finally:
            server_process.terminate()
            print("Server process terminated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a shard of the extraction pipeline.")
    parser.add_argument("--total-shards", type=int, required=True, help="The total number of parallel jobs (shards).")
    parser.add_argument("--shard-id", type=int, required=True, help="The 0-indexed ID of this job's shard.")
    parser.add_argument("--run-id", type=str, required=True, help="The run ID for this job, used for logging and tracking.")
    args = parser.parse_args()

    if args.shard_id >= args.total_shards:
        raise ValueError(f"Shard ID ({args.shard_id}) must be less than total shards ({args.total_shards}).")

    print(f"--- Running shard {args.shard_id} of {args.total_shards} ---")

    print("running extraction pipeline...")

    with init_server(f"output.{args.shard_id}.log", args.shard_id) as (server_process, llm_endpoint):
        if server_process is None or llm_endpoint is None:
            print("Failed to start the server. Exiting.")
            exit(1)

        print("Server started successfully. Running extraction pipeline...")

        try:
            main(args, llm_endpoint)    
        except Exception as e:
            traceback.print_exc()
            print(f"An error occurred during the extraction pipeline: {e}")
        finally:
            print("main pipeline finished, terminating server...")

    print("server terminated successfully.")