import argparse
import importlib.util
import time
from pathlib import Path

import pandas as pd

from utils.deepseek_client import append_jsonl, call_json, get_client, load_config


ROOT = Path(__file__).resolve().parents[1]
FAILED_PATH = ROOT / "04_extract_results" / "deepseek_review_failed_rows.xlsx"
RESULT_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
PROMPT_PATH = ROOT / "00_project_notes" / "ai_pathway_review_prompt.md"
RETRY_RAW_PATH = ROOT / "04_extract_results" / "deepseek_review_retry_raw_jsonl.jsonl"
PAPER_FAILED_PATH = ROOT / "05_statistics" / "deepseek_paper_summary_failed.xlsx"
PAPER_RESULT_PATH = ROOT / "05_statistics" / "paper_level_ai_summary.xlsx"
PAPER_RETRY_RAW_PATH = ROOT / "05_statistics" / "deepseek_paper_summary_retry_raw_jsonl.jsonl"
CONFLICT_FAILED_PATH = ROOT / "05_statistics" / "deepseek_conflict_resolution_failed.xlsx"
CONFLICT_RESULT_PATH = ROOT / "05_statistics" / "pathway_conflict_ai_resolved.xlsx"
CONFLICT_RETRY_RAW_PATH = ROOT / "05_statistics" / "deepseek_conflict_resolution_retry_raw_jsonl.jsonl"


def load_review_module():
    script_path = ROOT / "scripts" / "04b_deepseek_pathway_review.py"
    spec = importlib.util.spec_from_file_location("deepseek_pathway_review", script_path)
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {script_path}")
    spec.loader.exec_module(module)
    return module


def load_script_module(filename: str, module_name: str):
    script_path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {script_path}")
    spec.loader.exec_module(module)
    return module


def merge_rows(result_path: Path, new_rows: pd.DataFrame, key_cols: list[str]) -> None:
    if new_rows.empty:
        return
    current = pd.read_excel(result_path) if result_path.exists() else pd.DataFrame(columns=new_rows.columns)
    new_keys = set(zip(*(new_rows[col].astype(str) for col in key_cols)))
    if not current.empty:
        current = current[
            ~current.apply(lambda row: tuple(str(row[col]) for col in key_cols) in new_keys, axis=1)
        ]
    merged = pd.concat([current, new_rows], ignore_index=True)
    merged = merged.sort_values(key_cols).reset_index(drop=True)
    merged.to_excel(result_path, index=False)


def retry_sentence() -> None:
    if not FAILED_PATH.exists():
        print("No sentence-level failed rows file found.")
        return

    failed = pd.read_excel(FAILED_PATH)
    if failed.empty:
        print("No sentence-level failed rows to retry.")
        return

    config = load_config()
    client = get_client(config)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    review_module = load_review_module()
    rows = []
    still_failed = []
    batch_size = int(config.get("batch_size", 10))

    for start in range(0, len(failed), batch_size):
        batch = failed.iloc[start : start + batch_size].copy()
        try:
            parsed, raw = call_json(client, config, system_prompt, review_module.build_user_prompt(batch, config))
            batch_results = parsed.get("results")
            if not isinstance(batch_results, list):
                raise ValueError("DeepSeek batch response must contain a results list")
            append_jsonl(RETRY_RAW_PATH, {"batch_start": int(start), "batch_size": int(len(batch)), "parsed": parsed, "raw": raw})
            by_key = {
                (str(result.get("paper_id", "")), str(result.get("sentence_id", ""))): result
                for result in batch_results
                if isinstance(result, dict)
            }
            for _, row in batch.iterrows():
                key = (str(row.get("paper_id", "")), str(row.get("sentence_id", "")))
                if key not in by_key:
                    raise ValueError(f"Missing result for {key}")
                normalized = review_module.normalize_result(row, by_key[key])
                normalized["review_source"] = "deepseek_retry"
                rows.append(normalized)
        except Exception as exc:
            for _, row in batch.iterrows():
                item = row.to_dict()
                item["error"] = str(exc)
                still_failed.append(item)
        time.sleep(float(config.get("sleep_seconds", 0.5)))

    retry_df = pd.DataFrame(rows)
    merge_rows(RESULT_PATH, retry_df, ["paper_id", "sentence_id"])

    pd.DataFrame(still_failed).to_excel(FAILED_PATH, index=False)
    print(f"Retried sentence rows: {len(failed)}")
    print(f"Recovered rows: {len(retry_df)}")
    print(f"Still failed rows: {len(still_failed)} -> {FAILED_PATH.relative_to(ROOT)}")


def retry_paper() -> None:
    if not PAPER_FAILED_PATH.exists():
        print("No paper-level failed rows file found.")
        return
    failed = pd.read_excel(PAPER_FAILED_PATH)
    if failed.empty:
        print("No paper-level failed rows to retry.")
        return

    config = load_config()
    client = get_client(config)
    module = load_script_module("05b_deepseek_paper_level_summary.py", "deepseek_paper_summary")
    system_prompt = module.PROMPT_PATH.read_text(encoding="utf-8")
    sentence_df = pd.read_excel(module.SENTENCE_PATH)
    paper_df = pd.read_excel(module.PAPER_SUMMARY_PATH)
    metadata = module.load_metadata()
    paper_by_id = paper_df.set_index("paper_id")
    metadata_by_id = metadata.set_index("paper_id") if "paper_id" in metadata.columns else pd.DataFrame()
    rows = []
    still_failed = []

    for paper_id in failed["paper_id"].dropna().astype(str).unique():
        group = sentence_df[sentence_df["paper_id"].astype(str).eq(paper_id)]
        try:
            paper_row = paper_by_id.loc[paper_id].to_dict() if paper_id in paper_by_id.index else {}
            metadata_row = metadata_by_id.loc[paper_id].to_dict() if paper_id in metadata_by_id.index else {}
            parsed, raw = call_json(client, config, system_prompt, module.build_user_prompt(paper_id, group, paper_row, metadata_row))
            append_jsonl(PAPER_RETRY_RAW_PATH, {"paper_id": paper_id, "parsed": parsed, "raw": raw})
            rows.append(module.normalize_result(paper_id, parsed))
        except Exception as exc:
            still_failed.append({"paper_id": paper_id, "error": str(exc)})
        time.sleep(float(config.get("sleep_seconds", 0.5)))

    retry_df = pd.DataFrame(rows)
    merge_rows(PAPER_RESULT_PATH, retry_df, ["paper_id"])
    pd.DataFrame(still_failed).to_excel(PAPER_FAILED_PATH, index=False)
    print(f"Retried paper rows: {len(failed)}")
    print(f"Recovered papers: {len(retry_df)}")
    print(f"Still failed papers: {len(still_failed)} -> {PAPER_FAILED_PATH.relative_to(ROOT)}")


def retry_conflict() -> None:
    if not CONFLICT_FAILED_PATH.exists():
        print("No conflict failed rows file found.")
        return
    failed = pd.read_excel(CONFLICT_FAILED_PATH)
    if failed.empty:
        print("No conflict failed rows to retry.")
        return

    config = load_config()
    client = get_client(config)
    module = load_script_module("06b_deepseek_resolve_conflicts.py", "deepseek_conflict_resolution")
    system_prompt = module.PROMPT_PATH.read_text(encoding="utf-8")
    sentence_df = pd.read_excel(module.SENTENCE_PATH)
    paper_df = pd.read_excel(module.PAPER_PATH)
    sentence_by_paper = {paper_id: group for paper_id, group in sentence_df.groupby("paper_id")}
    paper_by_id = paper_df.set_index("paper_id")
    rows = []
    still_failed = []

    for _, conflict_row in failed.iterrows():
        paper_id = conflict_row.get("paper_id", "")
        try:
            sentence_group = sentence_by_paper.get(paper_id, pd.DataFrame(columns=sentence_df.columns))
            paper_row = paper_by_id.loc[paper_id].to_dict() if paper_id in paper_by_id.index else {}
            parsed, raw = call_json(client, config, system_prompt, module.build_user_prompt(conflict_row, sentence_group, paper_row))
            append_jsonl(CONFLICT_RETRY_RAW_PATH, {"paper_id": paper_id, "conflict_type": conflict_row.get("conflict_type", ""), "parsed": parsed, "raw": raw})
            rows.append(module.normalize_result(conflict_row, parsed))
        except Exception as exc:
            item = conflict_row.to_dict()
            item["error"] = str(exc)
            still_failed.append(item)
        time.sleep(float(config.get("sleep_seconds", 0.5)))

    retry_df = pd.DataFrame(rows)
    merge_rows(CONFLICT_RESULT_PATH, retry_df, ["paper_id", "conflict_type"])
    pd.DataFrame(still_failed).to_excel(CONFLICT_FAILED_PATH, index=False)
    print(f"Retried conflict rows: {len(failed)}")
    print(f"Recovered conflicts: {len(retry_df)}")
    print(f"Still failed conflicts: {len(still_failed)} -> {CONFLICT_FAILED_PATH.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retry failed DeepSeek rows and merge successful results.")
    parser.add_argument("--stage", choices=["sentence", "paper", "conflict", "all"], default="sentence")
    args = parser.parse_args()

    if args.stage in {"sentence", "all"}:
        retry_sentence()
    if args.stage in {"paper", "all"}:
        retry_paper()
    if args.stage in {"conflict", "all"}:
        retry_conflict()


if __name__ == "__main__":
    main()
