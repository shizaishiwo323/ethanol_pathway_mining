import re
from pathlib import Path

import pandas as pd
from tqdm import tqdm


ROOT = Path(__file__).resolve().parents[1]
TXT_DIR = ROOT / "03_text"
OUTPUT_PATH = ROOT / "04_extract_results" / "extracted_mechanism_sentences.xlsx"

TRIGGERS = [
    "ethanol",
    "C2H5OH",
    "mechanism",
    "pathway",
    "intermediate",
    "C-C coupling",
    "C–C coupling",
    "dimerization",
    "OCCO",
    "COCO",
    "CHO",
    "COH",
    "OCHO",
    "formate",
    "oxygenate",
]

PAGE_RE = re.compile(r"===== PAGE (\d+) =====")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(*])")


def split_page_blocks(text: str):
    parts = PAGE_RE.split(text)
    if len(parts) == 1:
        yield "", text
        return
    for index in range(1, len(parts), 2):
        page = parts[index]
        body = parts[index + 1] if index + 1 < len(parts) else ""
        yield page, body


def normalize_sentence(sentence: str) -> str:
    sentence = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", sentence)
    sentence = re.sub(r"\s+", " ", sentence)
    return sentence.strip()


def trigger_hits(sentence: str) -> list[str]:
    lower = sentence.lower()
    hits = []
    for trigger in TRIGGERS:
        if trigger.lower() in lower:
            hits.append(trigger)
    return hits


def paper_id_from_stem(stem: str) -> str:
    match = re.match(r"^(ETOH(?:_B2)?_\d+)", stem)
    return match.group(1) if match else stem


def main() -> None:
    rows = []
    txt_paths = sorted(TXT_DIR.glob("*.txt"))
    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    for txt_path in tqdm(txt_paths, desc="Extract sentences"):
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        paper_id = paper_id_from_stem(txt_path.stem)
        for page, body in split_page_blocks(text):
            body = re.sub(r"(\w)-\s+(\w)", r"\1\2", body)
            for raw_sentence in SENTENCE_RE.split(body):
                sentence = normalize_sentence(raw_sentence)
                if len(sentence) < 40:
                    continue
                hits = trigger_hits(sentence)
                if not hits:
                    continue
                rows.append(
                    {
                        "paper_id": paper_id,
                        "txt_name": txt_path.name,
                        "page": page,
                        "sentence": sentence,
                        "trigger_terms": "; ".join(hits),
                    }
                )

    df = pd.DataFrame(rows, columns=["paper_id", "txt_name", "page", "sentence", "trigger_terms"])
    df.drop_duplicates(subset=["paper_id", "sentence"], inplace=True)
    df.to_excel(OUTPUT_PATH, index=False)
    print(f"Extracted {len(df)} candidate sentences -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
