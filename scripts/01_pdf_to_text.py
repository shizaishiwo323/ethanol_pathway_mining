from pathlib import Path

import pdfplumber
from tqdm import tqdm


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_PDF_DIR = ROOT / "01_pdfs"
FALLBACK_PDF_DIR = ROOT / "paper_pdf_folder"
TXT_DIR = ROOT / "03_text"


def choose_pdf_dir() -> Path:
    primary_pdfs = list(PRIMARY_PDF_DIR.glob("*.pdf"))
    if primary_pdfs:
        return PRIMARY_PDF_DIR
    return FALLBACK_PDF_DIR


def main() -> None:
    pdf_dir = choose_pdf_dir()
    pdf_paths = sorted(pdf_dir.glob("*.pdf"))
    TXT_DIR.mkdir(exist_ok=True)

    if not pdf_paths:
        print(f"No PDF files found in {PRIMARY_PDF_DIR} or {FALLBACK_PDF_DIR}.")
        return

    for pdf_path in tqdm(pdf_paths, desc="PDF to text"):
        txt_path = TXT_DIR / f"{pdf_path.stem}.txt"
        if txt_path.exists() and txt_path.stat().st_size > 0:
            continue

        all_text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    all_text.append(f"\n\n===== PAGE {index} =====\n\n{text}")
            txt_path.write_text("\n".join(all_text), encoding="utf-8")
        except Exception as exc:
            print(f"Failed: {pdf_path.name}, error: {exc}")

    print(f"Text files written to {TXT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
