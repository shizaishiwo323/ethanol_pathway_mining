import os
import subprocess
import sys
from pathlib import Path


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


def main() -> None:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Export it before running the DeepSeek stage 4-6 workflow.")

    for script in STEPS:
        print(f"\n=== Running {script} ===", flush=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
