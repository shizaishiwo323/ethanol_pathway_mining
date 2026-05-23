from pathlib import Path

import pandas as pd
import pdfplumber
from tqdm import tqdm


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_PDF_DIR = ROOT / "01_pdfs"
FALLBACK_PDF_DIR = ROOT / "paper_pdf_folder"
TXT_DIR = ROOT / "03_text"
LOG_PATH = ROOT / "04_extract_results" / "pdf_conversion_log.xlsx"


def choose_pdf_dir() -> Path:
    primary_pdfs = list(PRIMARY_PDF_DIR.glob("*.pdf"))
    if primary_pdfs:
        return PRIMARY_PDF_DIR
    return FALLBACK_PDF_DIR


def main() -> None:
    pdf_dir = choose_pdf_dir()
    pdf_paths = sorted(pdf_dir.glob("*.pdf"))
    TXT_DIR.mkdir(exist_ok=True)
    LOG_PATH.parent.mkdir(exist_ok=True)
    log_rows = []

    if not pdf_paths:
        print(f"No PDF files found in {PRIMARY_PDF_DIR} or {FALLBACK_PDF_DIR}.")
        return

    for pdf_path in tqdm(pdf_paths, desc="PDF to text"):
        txt_path = TXT_DIR / f"{pdf_path.stem}.txt"
        if txt_path.exists() and txt_path.stat().st_size > 0:
            log_rows.append(
                {
                    "pdf_name": pdf_path.name,
                    "pdf_path": str(pdf_path.relative_to(ROOT)),
                    "txt_name": txt_path.name,
                    "status": "exists",
                    "page_count": "",
                    "character_count": txt_path.stat().st_size,
                    "error": "",
                }
            )
            continue

        all_text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    all_text.append(f"\n\n===== PAGE {index} =====\n\n{text}")
            txt_path.write_text("\n".join(all_text), encoding="utf-8")
            log_rows.append(
                {
                    "pdf_name": pdf_path.name,
                    "pdf_path": str(pdf_path.relative_to(ROOT)),
                    "txt_name": txt_path.name,
                    "status": "converted",
                    "page_count": len(pdf.pages),
                    "character_count": txt_path.stat().st_size,
                    "error": "",
                }
            )
        except Exception as exc:
            print(f"Failed: {pdf_path.name}, error: {exc}")
            log_rows.append(
                {
                    "pdf_name": pdf_path.name,
                    "pdf_path": str(pdf_path.relative_to(ROOT)),
                    "txt_name": txt_path.name,
                    "status": "failed",
                    "page_count": "",
                    "character_count": "",
                    "error": str(exc),
                }
            )

    pd.DataFrame(log_rows).to_excel(LOG_PATH, index=False)
    print(f"Text files written to {TXT_DIR.relative_to(ROOT)}")
    print(f"Conversion log -> {LOG_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
