import json
import re
from pathlib import Path

import pandas as pd
from tqdm import tqdm


ROOT = Path(__file__).resolve().parents[1]
TXT_DIR = ROOT / "03_text"
TRIGGERS_PATH = ROOT / "02_metadata" / "extraction_triggers.json"
RAW_OUTPUT_PATH = ROOT / "04_extract_results" / "extracted_mechanism_sentences_raw.xlsx"
OUTPUT_PATH = ROOT / "04_extract_results" / "extracted_mechanism_sentences.xlsx"

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


def load_triggers() -> dict[str, list[str]]:
    with TRIGGERS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def trigger_hits(sentence: str, triggers: dict[str, list[str]]) -> tuple[list[str], list[str], int]:
    lower = sentence.lower()
    hits = []
    categories = []
    for category, terms in triggers.items():
        category_hits = [term for term in terms if term.lower() in lower]
        if category_hits:
            hits.extend(category_hits)
            categories.append(category)
    score = len(hits) + len(categories)
    if "product_terms" in categories and ("mechanism_terms" in categories or "coupling_terms" in categories):
        score += 2
    if "pathway_terms" in categories and "coupling_terms" in categories:
        score += 2
    return hits, categories, score


def paper_id_from_stem(stem: str) -> str:
    match = re.match(r"^(ETOH(?:_B2)?_\d+)", stem)
    return match.group(1) if match else stem


def main() -> None:
    rows = []
    raw_rows = []
    triggers = load_triggers()
    txt_paths = sorted(TXT_DIR.glob("*.txt"))
    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    for txt_path in tqdm(txt_paths, desc="Extract sentences"):
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        paper_id = paper_id_from_stem(txt_path.stem)
        for page, body in split_page_blocks(text):
            body = re.sub(r"(\w)-\s+(\w)", r"\1\2", body)
            sentences = [normalize_sentence(item) for item in SENTENCE_RE.split(body)]
            sentences = [item for item in sentences if item]
            for index, sentence in enumerate(sentences):
                if len(sentence) < 40:
                    continue
                hits, categories, score = trigger_hits(sentence, triggers)
                if not hits:
                    continue
                row = (
                    {
                        "paper_id": paper_id,
                        "txt_name": txt_path.name,
                        "page": page,
                        "previous_sentence": sentences[index - 1] if index > 0 else "",
                        "sentence": sentence,
                        "next_sentence": sentences[index + 1] if index + 1 < len(sentences) else "",
                        "trigger_terms": "; ".join(hits),
                        "trigger_categories": "; ".join(categories),
                        "keyword_score": score,
                    }
                )
                raw_rows.append(row)
                rows.append(row)

    columns = [
        "paper_id",
        "txt_name",
        "page",
        "previous_sentence",
        "sentence",
        "next_sentence",
        "trigger_terms",
        "trigger_categories",
        "keyword_score",
    ]
    raw_df = pd.DataFrame(raw_rows, columns=columns)
    raw_df.to_excel(RAW_OUTPUT_PATH, index=False)

    df = pd.DataFrame(rows, columns=columns)
    df.drop_duplicates(subset=["paper_id", "sentence"], inplace=True)
    df.sort_values(["paper_id", "page", "keyword_score"], ascending=[True, True, False], inplace=True)
    df.to_excel(OUTPUT_PATH, index=False)
    print(f"Raw extracted rows: {len(raw_df)} -> {RAW_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Extracted {len(df)} candidate sentences -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
