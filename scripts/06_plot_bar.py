from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "04_extract_results" / "pathway_frequency_summary.xlsx"
OUTPUT_PATH = ROOT / "06_figures" / "pathway_frequency_bar.png"


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    labels = df["pathway_code"].tolist()
    x = range(len(labels))
    width = 0.38

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar([i - width / 2 for i in x], df["mentioned_count"], width=width, label="Mentioned")
    ax.bar([i + width / 2 for i in x], df["main_count"], width=width, label="Main")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Paper count")
    ax.set_xlabel("Pathway code")
    ax.set_title("Ethanol Formation Pathway Frequency")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=300)
    print(f"Bar figure -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
