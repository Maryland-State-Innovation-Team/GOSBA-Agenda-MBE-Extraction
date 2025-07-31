import os
import re
import pathlib
import pandas as pd
from tqdm import tqdm
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import pymupdf4llm
import json
import google
from google import genai
from google.genai.types import GenerateContentConfig

# --- Pydantic models ---
class MBESubGoal(BaseModel):
    demographic: str
    percent: Optional[float]

class CGLExtraction(BaseModel):
    grantee_name: str
    mbe_participation_goal: Optional[float]
    mbe_compliance: Optional[float]
    mbe_subgoals: List[MBESubGoal]

# --- Gemini client setup ---
def get_gemini_client(model_name="gemini-2.5-pro"):
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=GEMINI_API_KEY)
    return client

# --- System prompt ---
SYSTEM_PROMPT = '''
You are an expert in extracting structured data from government board meeting agendas. You will be given markdown text from one or more consecutive pages of a Maryland Board of Public Works agenda, specifically for a single CGL (Capital Grants and Loans) item. Extract the following fields as a valid JSON object matching the CGLExtraction pydantic model:
- grantee_name: The name of the grantee. This typically follows a phrase like "Recommendation: That the Board of Public Works enter into a grant agreement for the following grant: ".
- mbe_participation_goal: The MBE Participation Goal as a percent (e.g., 29.0 for 29%).
- mbe_compliance: The MBE Compliance percent (e.g., 29.0 for 29%).
- mbe_subgoals: A list of sub-goals, each with a demographic (e.g., "African-American", "Women-owned") and a percent (e.g., 7.0 for 7%).
Guidelines:
- Only extract data that is clearly present in the text. If a field is not present, leave it null or empty.
- Output must be valid JSON and match the CGLExtraction schema exactly.
'''

# --- PDF to markdown utility ---
def pdf_to_markdown_pages(pdf_path):
    data = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
    md_pages = []
    for i, page_data in enumerate(data):
        md = f"# Page {i+1}\n\n{page_data['text'].strip()}"
        md_pages.append((i+1, md))
    return md_pages

# --- Main extraction function ---
def extract_agenda_structured(
    pdf_folder="pdf_cache",
    output_csv="output/agenda_structured.csv",
    model_name="gemini-2.5-pro"
):
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    client = get_gemini_client(model_name)
    pdf_paths = sorted(pathlib.Path(pdf_folder).glob("*.pdf"))
    all_rows = []
    for pdf_path in tqdm(pdf_paths, desc="Processing PDFs"):
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})-agenda\.pdf", pdf_path.name)
        if not date_match:
            continue
        agenda_date = date_match.group(1)
        md_pages = pdf_to_markdown_pages(str(pdf_path))
        # Find CGL pages
        cgl_pages = {}
        for page_num, md in md_pages:
            if "-CGL." in md and "CAPITAL GRANTS AND LOANS" in md:
                cgl_matches = re.findall(r"(\d+-CGL\.)", md)
                for cgl in cgl_matches:
                    if cgl not in cgl_pages:
                        cgl_pages[cgl] = {"pages": [], "md": []}
                    cgl_pages[cgl]["pages"].append(page_num)
                    cgl_pages[cgl]["md"].append(md)
        # For each CGL, combine markdown and extract
        for cgl_number, info in cgl_pages.items():
            combined_md = "\n\n".join(info["md"])
            page_numbers = info["pages"]
            # --- LLM extraction ---
            response = client.models.generate_content(
                model=model_name,
                contents=combined_md,
                config=GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type='application/json',
                    response_schema=CGLExtraction
                ),
            )
            try:
                data = json.loads(response.text)
                extraction = CGLExtraction(**data)
            except Exception as e:
                print(f"[WARNING] Extraction failed for {pdf_path.name} {cgl_number}: {e}")
                continue
            # Flatten for CSV
            row = {
                "Date": agenda_date,
                "PageNumbers": "-".join([str(p) for p in list(set([min(page_numbers), max(page_numbers)]))]),
                "CGLNumber": cgl_number,
                "GranteeName": extraction.grantee_name,
                "MBEParticipationGoal": extraction.mbe_participation_goal,
                "MBECompliance": extraction.mbe_compliance
            }
            # Add sub-goals as columns
            for sub in extraction.mbe_subgoals:
                col = f"{sub.demographic} Participation Goal"
                row[col] = sub.percent
            all_rows.append(row)
            import pdb; pdb.set_trace()
    # Export to CSV
    df = pd.DataFrame(all_rows)
    df.to_csv(output_csv, index=False)
    print(f"Saved structured agenda extraction to {output_csv}")
