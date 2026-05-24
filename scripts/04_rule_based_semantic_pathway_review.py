"""Rule-based fallback for sentence-level pathway review.

The main stage 4-6 workflow should use 04b_deepseek_pathway_review.py when
DEEPSEEK_API_KEY is available. This script is retained as an offline fallback.
"""

from pathlib import Path
import runpy


SCRIPT = Path(__file__).with_name("04_codex_semantic_pathway_review.py")


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
