import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "03_rule_match_pathways.py",
    "04_prepare_ai_pathway_review.py",
    "04b_deepseek_pathway_review.py",
    "05_summarize_pathways_by_paper.py",
    "05b_deepseek_paper_level_summary.py",
    "06_check_pathway_conflicts.py",
    "06b_deepseek_resolve_conflicts.py",
    "07_calculate_pathway_frequency.py",
]

FAILED_CHECKS = {
    "04b_deepseek_pathway_review.py": ROOT / "04_extract_results" / "deepseek_review_failed_rows.xlsx",
    "05b_deepseek_paper_level_summary.py": ROOT / "05_statistics" / "deepseek_paper_summary_failed.xlsx",
    "06b_deepseek_resolve_conflicts.py": ROOT / "05_statistics" / "deepseek_conflict_resolution_failed.xlsx",
}


def failed_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(pd.read_excel(path))
    except ValueError:
        return 0


def main() -> None:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Export it before running the DeepSeek stage 4-6 workflow.")

    for script in STEPS:
        print(f"\n=== Running {script} ===", flush=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)
        if script in FAILED_CHECKS and not os.environ.get("ALLOW_FAILED_DEEPSEEK_ROWS"):
            count = failed_count(FAILED_CHECKS[script])
            if count:
                raise RuntimeError(
                    f"{FAILED_CHECKS[script].relative_to(ROOT)} contains {count} failed rows. "
                    "Run scripts/retry_deepseek_failures.py or set ALLOW_FAILED_DEEPSEEK_ROWS=1 to continue anyway."
                )


if __name__ == "__main__":
    main()
