import os
import json
import glob
import argparse


def merge_json_shards(file_paths, output_path):
    """
    Reads a list of JSON files, each containing a list of objects,
    and merges them into a single list in a new JSON file.

    Args:
        file_paths (list): A list of full paths to the JSON shard files.
        output_path (str): The full path for the merged output JSON file.
    """
    merged_data = []
    
    # Sort files for deterministic order, although not strictly necessary
    for file_path in sorted(file_paths):
        print(f"  - Reading {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Load the JSON data, which is expected to be a list
                data = json.load(f)
                if isinstance(data, list):
                    # Extend the main list with the list from the file
                    merged_data.extend(data)
                else:
                    print(f"    - WARNING: File did not contain a list. Skipping: {file_path}")
        except json.JSONDecodeError:
            print(f"    - ERROR: Could not decode JSON. File may be corrupt. Skipping: {file_path}")
        except Exception as e:
            print(f"    - ERROR: An unexpected error occurred with file {file_path}: {e}")

    print(f"Total objects merged: {len(merged_data)}")
    print(f"Writing merged data to: {output_path}")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the merged list to the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        # Use indent for a human-readable output file
        json.dump(merged_data, f, indent=2)

    print("Write complete.")

def main(run_id: str):
  """
  Finds all 'notes' and 'patients' JSON shards, and merges each type
  into a single, consolidated JSON file.
  """
  # in the folder are two types of files: - patient and note
  # e.g. notes_shard_0_of_20.json and patients_shard_0_of_20.json
  # find all files, and merge them into one file in the OUT_DIR
  # both are arrays of objects.

  # Use glob to easily find all files matching a pattern
  #           /sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/shards/193082461
  INP_DIR = f"/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/shards/{run_id}"
  OUT_DIR  = f"/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/processed/merged_shards/{run_id}"


  note_files = glob.glob(os.path.join(INP_DIR, "notes_shard_*.json"))
  patient_files = glob.glob(os.path.join(INP_DIR, "patients_shard_*.json"))

  print(f"Found {len(note_files)} note files and {len(patient_files)} patient files in {INP_DIR}\n")

  # --- Merge Note Files ---
  if note_files:
    print("Starting merge for NOTE files...")
    notes_output_path = os.path.join(OUT_DIR, "notes.json")
    merge_json_shards(note_files, notes_output_path)
  else:
    print("No note files found to merge.")

  print("-" * 40)

  # --- Merge Patient Files ---
  if patient_files:
    print("Starting merge for PATIENT files...")
    patients_output_path = os.path.join(OUT_DIR, "patients.json")
    merge_json_shards(patient_files, patients_output_path)
  else:
    print("No patient files found to merge.")
    
  print("\nScript finished successfully.")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Run a shard of the extraction pipeline.")
  parser.add_argument("--run-id", type=str, required=True, help="The run ID for this job, used for logging and tracking.")
  args = parser.parse_args()
  args.run_id = args.run_id.strip()  # Ensure no leading/trailing whitespace
  print(f"Running merge script for run ID: {args.run_id}")
  main(args.run_id)