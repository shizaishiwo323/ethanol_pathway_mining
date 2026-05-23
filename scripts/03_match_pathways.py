import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
KEYWORDS_PATH = ROOT / "02_metadata" / "pathway_keywords.json"
INPUT_PATH = ROOT / "04_extract_results" / "extracted_mechanism_sentences.xlsx"
OUTPUT_PATH = ROOT / "04_extract_results" / "auto_pathway_matches.xlsx"
TEMPLATE_PATH = ROOT / "05_manual_check" / "manual_annotation_template.xlsx"
MANUAL_CHECK_PATH = ROOT / "05_manual_check" / "manual_check.xlsx"


def keyword_pattern(keyword: str) -> re.Pattern:
    escaped = re.escape(keyword)
    escaped = escaped.replace("\\-", "[-–]")
    return re.compile(escaped, flags=re.IGNORECASE)


def find_matches(sentence: str, keywords: dict[str, list[str]]) -> tuple[str, str]:
    matched_codes = []
    matched_terms = []
    for code, terms in keywords.items():
        code_terms = []
        for term in terms:
            if keyword_pattern(term).search(sentence):
                code_terms.append(term)
        if code_terms:
            matched_codes.append(code)
            matched_terms.extend(f"{code}:{term}" for term in code_terms)
    return ";".join(matched_codes), "; ".join(matched_terms)


def main() -> None:
    with KEYWORDS_PATH.open(encoding="utf-8") as f:
        keywords = json.load(f)
    df = pd.read_excel(INPUT_PATH)

    matches = df["sentence"].fillna("").apply(lambda value: find_matches(value, keywords))
    df["auto_matched_pathway"] = [item[0] for item in matches]
    df["matched_keywords"] = [item[1] for item in matches]
    df = df[df["auto_matched_pathway"].astype(str).str.len() > 0].copy()
    df["manual_pathway"] = ""
    df["role"] = ""
    df["ethanol_specific"] = ""
    df["confidence"] = ""
    df["notes"] = ""

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    TEMPLATE_PATH.parent.mkdir(exist_ok=True)
    df.to_excel(OUTPUT_PATH, index=False)
    df.head(0).to_excel(TEMPLATE_PATH, index=False)
    df.to_excel(MANUAL_CHECK_PATH, index=False)

    print(f"Matched {len(df)} sentences -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Manual review copy -> {MANUAL_CHECK_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
