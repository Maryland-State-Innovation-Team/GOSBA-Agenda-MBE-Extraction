# GOSBA-Agenda-MBE-Extraction
AI data pipeline for extracting MBE goals and compliance rates from agenda PDFs

## Overview
This project automates the extraction of Minority Business Enterprise (MBE) participation goals and compliance rates from Maryland Board of Public Works agenda PDFs. It uses Google Gemini and modern PDF parsing to produce structured CSV outputs for analysis.

## Setup Instructions

### 1. Clone the Repository
```powershell
git clone https://github.com/Maryland-State-Innovation-Team/GOSBA-Agenda-MBE-Extraction.git
cd GOSBA-Agenda-MBE-Extraction
```

### 2. Create and Activate a Virtual Environment (Windows)
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
- Copy `.env-example` to `.env`:
  ```powershell
  copy .env-example .env
  ```
- Open `.env` and add your Gemini API key:
  ```env
  GEMINI_API_KEY=your_actual_api_key_here
  ```

## Usage

1. **Download Agenda PDFs**
   - Run the agenda downloader for each year (uncomment in `main.py`):
     ```python
     for year in range(2020, 2026):
         download_agendas_from_html_input(year)
     ```
   - Follow the prompts to paste HTML and download PDFs into the `pdf_cache` folder.

2. **Extract Structured Data**
   - Run the main pipeline:
     ```powershell
     python -m pipeline.main
     ```
   - The output CSV will be saved in the `output` folder as `agenda_structured.csv`.

## Notes
- Requires a valid Gemini API key for LLM extraction.
- PDF parsing uses `pymupdf4llm` for robust text extraction.
- The pipeline is designed for Windows but can be adapted for other OSes.

## Troubleshooting
- If you encounter missing dependencies, ensure your virtual environment is activated and run `pip install -r requirements.txt` again.
- For API errors, double-check your `.env` file and API key.
