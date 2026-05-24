import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
KEYWORDS_PATH = ROOT / "02_metadata" / "pathway_keywords.json"
INPUT_PATH = ROOT / "04_extract_results" / "ai_mechanism_sentence_candidates.xlsx"
OUTPUT_PATH = ROOT / "04_extract_results" / "03_rule_pathway_matches.xlsx"


def keyword_pattern(keyword: str) -> re.Pattern:
    escaped = re.escape(keyword.strip())
    escaped = escaped.replace(r"\-", "[-–]")
    escaped = escaped.replace(r"\ ", r"\s*")
    if keyword == "*COH":
        escaped = escaped + r"(?!ydrogenation)"
    return re.compile(escaped, flags=re.IGNORECASE)


def find_matches(text: str, keywords: dict[str, list[str]]) -> tuple[str, str]:
    matched_codes = []
    matched_terms = []
    for code, terms in keywords.items():
        code_terms = []
        for term in terms:
            if keyword_pattern(term).search(text):
                code_terms.append(term)
        if code_terms:
            matched_codes.append(code)
            matched_terms.extend(f"{code}:{term}" for term in code_terms)
    return ";".join(matched_codes), "; ".join(matched_terms)


def needs_ai_review(row: pd.Series) -> str:
    if str(row.get("ai_relevant", "")).strip().lower() == "yes":
        return "yes"
    if str(row.get("rule_matched_pathways", "")).strip():
        return "yes"
    return "no"


def main() -> None:
    with KEYWORDS_PATH.open(encoding="utf-8") as f:
        keywords = json.load(f)

    df = pd.read_excel(INPUT_PATH)
    if "sentence_id" not in df.columns:
        df.insert(2, "sentence_id", [f"S{i:04d}" for i in range(1, len(df) + 1)])

    text_for_match = df["sentence"].fillna("").astype(str)
    matches = text_for_match.apply(lambda value: find_matches(value, keywords))
    df["matched_keywords"] = [item[1] for item in matches]
    df["rule_matched_pathways"] = [item[0] for item in matches]
    df["rule_match_count"] = df["rule_matched_pathways"].apply(
        lambda value: 0 if not str(value).strip() else len(str(value).split(";"))
    )
    df["needs_ai_review"] = df.apply(needs_ai_review, axis=1)

    keep_cols = [
        "paper_id",
        "txt_name",
        "sentence_id",
        "page",
        "previous_sentence",
        "sentence",
        "next_sentence",
        "ai_relevant",
        "relevance_level",
        "sentence_type",
        "ethanol_specific",
        "oxygenate_related",
        "matched_keywords",
        "rule_matched_pathways",
        "rule_match_count",
        "needs_ai_review",
    ]
    out = df[[col for col in keep_cols if col in df.columns]].copy()
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    out.to_excel(OUTPUT_PATH, index=False)
    print(f"Rule pathway matches: {len(out)} rows -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Rows needing AI review: {(out['needs_ai_review'] == 'yes').sum()}")


if __name__ == "__main__":
    main()
