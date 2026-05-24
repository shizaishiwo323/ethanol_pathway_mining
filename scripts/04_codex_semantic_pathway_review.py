import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "04_extract_results" / "03_rule_pathway_matches.xlsx"
OUTPUT_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"


MAIN_CUES = [
    "we propose",
    "we suggest",
    "we demonstrate",
    "results indicate",
    "result indicates",
    "results reveal",
    "revealed",
    "confirm",
    "confirmed",
    "attributed to",
    "follows",
    "proceeds through",
    "preferred pathway",
    "dominant pathway",
    "favorable pathway",
    "facilitated",
    "promotes",
    "boosting",
]
COMPARE_CUES = ["compared", "whereas", "while", "on the other hand", "respectively", "contrast"]
REJECT_CUES = ["unfavorable", "unlikely", "excluded", "suppressed", "inhibited", "hindered", "not favorable"]


def split_codes(value) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def infer_extra_codes(text: str) -> set[str]:
    compact = re.sub(r"\s+", "", text).lower()
    codes = set()
    if any(term in compact for term in ["*occo", "occo", "*coco", "coco"]):
        codes.add("P1")
    if any(term in compact for term in ["*co-*cho", "*co–*cho", "co-cho", "co–cho", "*cho"]):
        codes.add("P2")
    if any(term in compact for term in ["*co-*coh", "*co–*coh", "co-coh", "co–coh"]):
        codes.add("P3")
    if "*coh" in compact and "*cohydrogenation" not in compact:
        codes.add("P3")
    if any(term in compact for term in ["co-chx", "co–chx", "*chx", "*ch2", "*ch3"]):
        codes.add("P4")
    if any(term in compact for term in ["*ocho", "ocho", "hcoo", "formate"]):
        codes.add("P5")
    return codes


def infer_ethanol_specific(row: pd.Series, text: str) -> str:
    source_label = str(row.get("ethanol_specific", "")).strip().lower()
    lower = text.lower()
    if source_label == "yes" or "ethanol" in lower or "c2h5oh" in lower:
        return "yes"
    if source_label == "no":
        return "no"
    if str(row.get("oxygenate_related", "")).strip().lower() == "yes":
        return "unclear"
    return "unclear"


def infer_evidence_type(text: str) -> str:
    lower = text.lower()
    evidence = []
    if any(term in lower for term in ["dft", "theoretical", "calculation", "gibbs", "free energy", "energy barrier"]):
        evidence.append("DFT")
    if any(term in lower for term in ["in situ", "in-situ", "operando", "raman", "ftir", "xas", "xps", "spectra"]):
        evidence.append("operando/spectroscopy")
    if any(term in lower for term in ["isotope", "13c", "c-13"]):
        evidence.append("isotope")
    if any(term in lower for term in ["faradaic", "selectivity", "product distribution", "ethanol-to-ethylene"]):
        evidence.append("product inference")
    if not evidence and any(term in lower for term in ["reported", "proposed", "review", "literature"]):
        evidence.append("review")
    return ";".join(evidence) if evidence else "unknown"


def infer_role(text: str, codes: set[str], ethanol: str) -> str:
    lower = text.lower()
    if not codes:
        return "unclear"
    if any(cue in lower for cue in REJECT_CUES):
        return "reject"
    if len(codes) > 1 and any(cue in lower for cue in COMPARE_CUES):
        return "compare"
    if ethanol == "yes" and any(cue in lower for cue in MAIN_CUES):
        return "main"
    if any(cue in lower for cue in ["pathway", "mechanism", "coupling", "intermediate"]):
        return "mention"
    return "unclear"


def infer_confidence(row: pd.Series, codes: set[str], role: str, ethanol: str) -> str:
    relevance = str(row.get("relevance_level", "")).strip().lower()
    match_count = int(row.get("rule_match_count", 0) or 0)
    if not codes or role == "unclear":
        return "low"
    if role == "main" and ethanol == "yes" and relevance == "high" and match_count >= 1:
        return "high"
    if ethanol == "yes" and match_count >= 1:
        return "medium"
    return "low"


def reason_for(row: pd.Series, codes: set[str], role: str, ethanol: str, evidence_type: str) -> str:
    if not codes:
        return "No P1-P6 pathway cue was specific enough for final pathway assignment."
    if role == "main":
        return f"Sentence links {','.join(sorted(codes))} to ethanol mechanism with author-supported evidence ({evidence_type})."
    if role == "compare":
        return f"Sentence compares multiple pathway cues ({','.join(sorted(codes))}) without assigning a single dominant route."
    if role == "reject":
        return f"Sentence uses negative feasibility language for {','.join(sorted(codes))}."
    if role == "mention":
        return f"Sentence mentions pathway cue(s) {','.join(sorted(codes))}; support for a main ethanol route is not explicit."
    return f"Pathway cue(s) {','.join(sorted(codes))} appear, but ethanol specificity is {ethanol} or context is insufficient."


def review_row(row: pd.Series) -> dict:
    context_text = " ".join(
        str(row.get(col, "") or "")
        for col in ["previous_sentence", "sentence", "next_sentence"]
        if str(row.get(col, "") or "").lower() != "nan"
    )
    sentence_text = str(row.get("sentence", "") or "")
    codes = set(split_codes(row.get("rule_matched_pathways"))) | infer_extra_codes(sentence_text)
    ethanol = infer_ethanol_specific(row, context_text)
    role = infer_role(context_text, codes, ethanol)
    evidence_type = infer_evidence_type(context_text)
    confidence = infer_confidence(row, codes, role, ethanol)
    include = "yes" if role in {"mention", "main", "compare"} and ethanol == "yes" and codes else "no"

    return {
        "paper_id": row.get("paper_id", ""),
        "txt_name": row.get("txt_name", ""),
        "sentence_id": row.get("sentence_id", ""),
        "sentence": row.get("sentence", ""),
        "rule_matched_pathways": row.get("rule_matched_pathways", ""),
        "matched_keywords": row.get("matched_keywords", ""),
        "ai_final_pathway": ";".join(sorted(codes)),
        "ai_role": role,
        "ai_ethanol_specific": ethanol,
        "ai_evidence_type": evidence_type,
        "ai_evidence_reason": reason_for(row, codes, role, ethanol, evidence_type),
        "ai_confidence": confidence,
        "ai_include_in_statistics": include,
    }


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    reviewed = pd.DataFrame([review_row(row) for _, row in df.iterrows()])
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    reviewed.to_excel(OUTPUT_PATH, index=False)
    print(f"Codex semantic pathway review rows: {len(reviewed)} -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(reviewed[["ai_role", "ai_include_in_statistics"]].value_counts().to_string())


if __name__ == "__main__":
    main()
