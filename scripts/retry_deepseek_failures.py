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


def load_review_module():
    script_path = ROOT / "scripts" / "04b_deepseek_pathway_review.py"
    spec = importlib.util.spec_from_file_location("deepseek_pathway_review", script_path)
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {script_path}")
    spec.loader.exec_module(module)
    return module


def main() -> None:
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

    current = pd.read_excel(RESULT_PATH)
    retry_df = pd.DataFrame(rows)
    if not retry_df.empty:
        retry_keys = set(zip(retry_df["paper_id"].astype(str), retry_df["sentence_id"].astype(str)))
        current = current[
            ~current.apply(lambda row: (str(row["paper_id"]), str(row["sentence_id"])) in retry_keys, axis=1)
        ]
        current = pd.concat([current, retry_df], ignore_index=True)
        current = current.sort_values(["paper_id", "sentence_id"]).reset_index(drop=True)
        current.to_excel(RESULT_PATH, index=False)

    pd.DataFrame(still_failed).to_excel(FAILED_PATH, index=False)
    print(f"Retried sentence rows: {len(failed)}")
    print(f"Recovered rows: {len(retry_df)}")
    print(f"Still failed rows: {len(still_failed)} -> {FAILED_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
