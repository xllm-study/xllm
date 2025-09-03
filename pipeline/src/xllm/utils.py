from datetime import datetime
import pandas as pd
from typing import Any, List, TypedDict, Dict, Optional, Union
from dataclasses import dataclass

class Chunk(TypedDict):
    text: str
    source_note_ids: List[int]


class MRNChunks(TypedDict):
    MRN: str
    chunks: List[Chunk]


class Run(TypedDict):
    note_ids: List[int]
    result: dict


class RunResult(TypedDict):
    mrn: str
    runs: List[Run]


def get_notes(file_location: str):
    # import using pandas
    notes = pd.read_csv(file_location, dtype={"NOTE_ID": int, "MRN": int, "NOTE_TEXT": str, "NOTE_DATE": str})
    assert "NOTE_ID" in notes.columns
    assert "MRN" in notes.columns
    assert "NOTE_TEXT" in notes.columns
    assert "NOTE_DATE" in notes.columns
    notes = notes.drop_duplicates(subset="NOTE_TEXT").reset_index(drop=True)
    notes = notes.sort_values(["MRN", "NOTE_DATE"]).reset_index(drop=True)
    return notes


def get_patient_meta(file_location: str):
    # import using pandas
    meta = pd.read_csv(file_location)
    assert "MRN" in meta.columns
    assert "LAST_NAME" in meta.columns
    assert "FIRST_NAME" in meta.columns
    assert "DATE_OF_BIRTH" in meta.columns
    assert "GENDER" in meta.columns
    
    return meta

@dataclass
class PatientMeta():
    last_name: str
    first_name: str
    date_of_birth: str
    """Patient's date of birth in YYYY-MM-DD format."""
    gender: str


def get_patient_meta_dict(file_location: str) -> Dict[int, PatientMeta]:
    meta_df = get_patient_meta(file_location)
    meta_dict = {}
    for _, row in meta_df.iterrows():
        mrn = row["MRN"]
        meta_dict[mrn] = PatientMeta(
            last_name=row["LAST_NAME"],
            first_name=row["FIRST_NAME"],
            date_of_birth=row["DATE_OF_BIRTH"],
            gender=row["GENDER"]
        )
    return meta_dict



def get_patient_meta_prompt(meta: PatientMeta) -> str:
    return f"<patient DoB=\"{meta.date_of_birth}\"/>"



def chunk_notes(notes: pd.DataFrame, chunk_max_chars: int) -> List[MRNChunks]:
    """
    Creates chunks of notes for each mrn, where each chunk has at most chunk_max_chars characters.
    Notes are never split across chunks.
    Returns an array of dicts with MRN and an array of chunks. Each chunk is a dict with text and source_note_ids.
    """
    assert "NOTE_ID" in notes.columns
    assert "MRN" in notes.columns
    assert "NOTE_TEXT" in notes.columns

    # sort notes by MRN
    notes = notes.sort_values("MRN").reset_index(drop=True)

    result = []
    curr_mrn = None
    curr_chunks = []
    curr_chunk_text = ""
    curr_chunk_note_ids = []

    for i, row in notes.iterrows():
        note = row["NOTE_TEXT"].strip()
        note_id = row["NOTE_ID"]
        note_wrapped = f'<note id="{note_id}">{note}</note>'

        if curr_mrn is None:
            curr_mrn = row["MRN"]

        is_last_note = i == notes.shape[0] - 1
        is_new_mrn = row["MRN"] != curr_mrn
        fits_current_chunk = len(curr_chunk_text) + len(note_wrapped) <= chunk_max_chars

        if is_new_mrn or (not fits_current_chunk and len(curr_chunk_text) > 0):
            curr_chunks.append(
                {"text": curr_chunk_text, "source_note_ids": curr_chunk_note_ids}
            )
            if is_new_mrn:
                result.append({"MRN": curr_mrn, "chunks": curr_chunks})
                curr_chunks = []
            curr_chunk_text = ""
            curr_chunk_note_ids = []
            curr_mrn = row["MRN"]

        curr_chunk_text += note_wrapped
        curr_chunk_note_ids.append(note_id)

        if is_last_note:
            curr_chunks.append(
                {"text": curr_chunk_text, "source_note_ids": curr_chunk_note_ids}
            )
            result.append({"MRN": curr_mrn, "chunks": curr_chunks})

    return result


# def extract_variables[T](
#     chunks: List[MRNChunks], ExtractorClass: T, client: OpenAI, model: str = "llama3.2"
# ):
#     """
#     Extract variables from a set of chunks using a given extractor class

#     Args:
#         chunks (List[MRNChunks]): A list of MRNChunks containing MRN and chunks of notes
#         extractor_class (class): The class to use for extracting variables, inheriting from a Pydantic BaseModel
#         client (OpenAI): The OpenAI client
#         model (str): The model to use for extracting variables

#     Returns:
#         Tuple[pd.DataFrame, List[dict]]: A tuple containing two DataFrames:
#             - The first DataFrame contains the extracted variables, one row per MRN.
#             - The second DataFrame contains the runs with note IDs and results.
#     """
#     extracted = []
#     runs = []

#     # make sure the folder exists
#     os.makedirs("extracted_chunks", exist_ok=True)

#     for mrn_chunk in chunks:
#         mrn = mrn_chunk["MRN"]
#         mrn_variables = []
#         mrn_runs: List[dict] = []

#         for chunk in tqdm(mrn_chunk["chunks"], desc=f"Processing MRN {mrn}"):
#             notes = chunk["text"]
#             notes += f"\n<schema>{ExtractorClass.schema_json()}</schema>"

#             completion = client.beta.chat.completions.parse(
#                 model=model,
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You're a medical professional tasked with extracting variables from medical notes. If some variable is not present in the notes, you don't need to provide a value in the response.",
#                     },
#                     {"role": "user", "content": notes},
#                 ],
#                 extra_body=dict(truncate_prompt_tokens=5000),
#                 response_format=ExtractorClass,
#             )

#             try:
#                 result = completion.choices[0].message

#                 if result.refusal:
#                     print(
#                         f"Refusal for MRN {mrn} with note IDs {chunk['source_note_ids']}"
#                     )
#                     continue
#                 else:
#                     mrn_variables.append(result.parsed)
#                     mrn_runs.append(
#                         {
#                             "note_ids": chunk["source_note_ids"],
#                             "result": result.parsed.to_enum_names(),
#                         }
#                     )

#             except ValidationError as e:
#                 # Handle validation errors
#                 print(e.json())

#         # merge variables from all executions
#         merged = ExtractorClass.merge(mrn_variables)
#         computed = process_computed_vars([v.to_enum_names(True) for v in mrn_variables])

#         extracted.append({"mrn": mrn} | merged.to_redcap_fields() | computed)
#         runs.append(
#             {
#                 "mrn": mrn,
#                 "runs": mrn_runs,
#                 "merged": merged.to_enum_names(True),
#                 "computed": computed,
#             }
#         )

#     return (
#         pd.DataFrame(extracted),
#         runs,
#     )


def get_ground_truth(file_location: str):
    # import using pandas
    notes = pd.read_csv(file_location, delimiter=",")
    cols = [
        "mrn",
        "cd_fm_hx",
        "uc_ic_fm_hx",
        "ibdu_fam_hx",
        "type_family_crc",
        "type_family_noncrc",
        "type_cancer",
        "smoking_history",
        "fam_hx_ibd",
        "fam_hx_ca",
        "fam_colorectal",
        "noncolorectal",
        "pers_hx_cancer",
    ]

    for col in cols:
        assert col in notes.columns

    return notes

def strip_titles_and_refs(schema: dict) -> dict:
    # Flatten $defs (formerly definitions)
    definitions = schema.pop("$defs", {})

    def resolve(obj: Union[dict, list, str]) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.split("/")[-1]
                    return resolve(definitions[def_name])
            return {
                k: resolve(v)
                for k, v in obj.items()
                if k != "title"
            }
        elif isinstance(obj, list):
            return [resolve(item) for item in obj]
        return obj

    return resolve(schema)


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parses partial ISO (YYYY, YYYY-MM, YYYY-MM-DD) and american dates(mm/dd/yyyy) 
    and returns them in ISO format (YYYY-MM-DD).
    e.g. "2023-10-26" -> "2023-10-26"
    "2020" -> "2020-01-01"
    "2021-05" -> "2021-05-01"
    "05/31/2022" -> "2022-05-31"
    Invalid or unsupported formats will return None.
    """
    # A list of date formats to try, ordered from most specific to least specific.
    # This order is important to parse correctly.
    formats_to_try = [
        '%Y-%m-%d',  # YYYY-MM-DD
        '%m/%d/%Y',  # mm/dd/yyyy
        '%Y-%m',     # YYYY-MM (defaults to the 1st day of the month)
        '%Y',        # YYYY (defaults to Jan 1st)
    ]

    if not date_str:
        return None

    for fmt in formats_to_try:
        try:
            # Attempt to parse the string with the current format
            parsed_date = datetime.strptime(date_str, fmt)
            # If successful, format it to the target ISO format and return
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            # If the format does not match, a ValueError is raised.
            # We catch it and simply try the next format in the list.
            continue
    
    # If the loop completes without returning, no format matched.
    return None