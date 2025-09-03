import datetime
from openai import OpenAI
from pydantic import ValidationError
from tqdm import tqdm
from pandas import pd
import os


def extract_variables[T](
    chunks: pd.DataFrame, ExtractorClass: T, client: OpenAI, model: str = "llama3.2"
):
    """
    Extract variables from a set of chunks using a given extractor class

    Args:
        chunks (pd.DataFrame): A DataFrame containing chunks of notes
        extractor_class (class): The class to use for extracting variables, inheriting from a Pydantic BaseModel
        client (OpenAI): The OpenAI client
        model (str): The model to use for extracting variables

    Returns:
        pd.DataFrame: A DataFrame containing the extracted variables, one row per mrn

    """
    assert "CHUNK_ID" in chunks.columns
    assert "MRN" in chunks.columns
    assert "NOTES" in chunks.columns

    #  list of extracted variables for each mrn
    extracted = []
    inference_runs = []

    # make sure the folder exists
    os.makedirs("extracted_chunks", exist_ok=True)

    mrnnum = 0

    # for each mrn and for each chunk of that mrn, extract the variables
    for mrn in chunks["MRN"].unique():
        # for mrn in chunks['MRN'].unique():
        mrnnum += 1
        mrn_variables = []
        mrn_chunks = chunks[chunks["MRN"] == mrn]
        for i, row in tqdm(
            mrn_chunks.iterrows(),
            desc=f"mrn {mrnnum} - note chunk",
            total=mrn_chunks.shape[0],
        ):
            notes = row["NOTES"]
            # add schema to notes
            notes += f"\n<schema>{ExtractorClass.schema_json()}</schema>"

            completion = client.beta.chat.completions.parse(
                model=model,
                # max_tokens=3412,
                # max
                messages=[
                    {
                        "role": "system",
                        "content": "You're a medical professional tasked with extracting variables from medical notes. If some variable is not present in the notes, you don't need to provide a value in the response.",
                    },
                    {"role": "user", "content": notes},
                ],
                extra_body=dict(truncate_prompt_tokens=3700),
                response_format=ExtractorClass,
            )

            try:
                result = completion.choices[0].message

                if result.refusal:
                    inference_runs.append(
                        {"mrn": mrn, "notes": notes, "error": result.refusal}
                    )
                    continue
                else:
                    # print(result.parsed)
                    mrn_variables.append(result.parsed)
                    inference_runs.append(
                        {
                            "mrn": mrn,
                            "notes": notes,
                            "result": result.parsed,
                        }
                    )

            except ValidationError as e:
                # Handle validation errors
                print(e.json())
                inference_runs.append(
                    {
                        "mrn": mrn,
                        "notes": notes,
                        "error": e.json(),
                    }
                )

        # merge variables from all executions
        merged = ExtractorClass.merge(mrn_variables)
        extracted.append({"mrn": mrn} | merged.to_redcap_fields())

    # store to file chunk + result
    isoDate = f"{datetime.utcnow().isoformat()[:-10]}Z"

    with open(f"extracted_chunks/run_{isoDate}.csv", "w") as f:
        # write the inference_runs as csv
        pd.DataFrame(inference_runs).to_csv(f)

    return pd.DataFrame(extracted)
