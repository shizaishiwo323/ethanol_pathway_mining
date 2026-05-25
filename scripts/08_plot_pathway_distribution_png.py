from pathlib import Path
import textwrap

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FREQ_PATH = ROOT / "05_statistics" / "pathway_frequency_summary.xlsx"
OUTPUT_PATH = ROOT / "06_figures" / "pathway_distribution_first_version.png"


PATHWAY_ORDER = ["P1", "P2", "P3", "P4", "P5", "P6"]
SHORT_LABELS = {
    "P1": "*CO dimerization",
    "P2": "CO-CHO coupling",
    "P3": "CO-COH coupling",
    "P4": "CO-CHx coupling",
    "P5": "OCHO/formate",
    "P6": "mixed/unclear",
}


def setup_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Hiragino Sans GB",
                "PingFang SC",
                "Arial Unicode MS",
                "Arial",
                "Helvetica",
                "DejaVu Sans",
                "sans-serif",
            ],
            "axes.unicode_minus": False,
            "font.size": 7,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.8,
            "axes.labelsize": 7.5,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.frameon": False,
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "savefig.facecolor": "white",
        }
    )


def load_plot_data() -> pd.DataFrame:
    freq = pd.read_excel(FREQ_PATH)
    freq = freq[freq["pathway_code"].isin(PATHWAY_ORDER)].copy()
    freq["pathway_code"] = pd.Categorical(freq["pathway_code"], PATHWAY_ORDER, ordered=True)
    freq = freq.sort_values("pathway_code").reset_index(drop=True)
    freq["pathway_label"] = [
        f"{row.pathway_code}\n{textwrap.fill(SHORT_LABELS.get(str(row.pathway_code), ''), width=15)}"
        for row in freq.itertuples()
    ]
    return freq


def annotate_bars(ax: plt.Axes, bars, total: int) -> None:
    for bar in bars:
        height = int(bar.get_height())
        if height <= 0:
            continue
        pct = 100 * height / total if total else 0
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.16,
            f"{height}\n{pct:.0f}%",
            ha="center",
            va="bottom",
            fontsize=5.8,
            linespacing=0.9,
        )


def main() -> None:
    setup_style()
    df = load_plot_data()
    total = int(df["total_valid_papers"].max())

    x = np.arange(len(df))
    width = 0.34
    mentioned_color = "#8DA9C4"
    main_color = "#D08B73"

    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    mentioned = ax.bar(
        x - width / 2,
        df["mentioned_paper_count"],
        width=width,
        color=mentioned_color,
        edgecolor="#374151",
        linewidth=0.35,
        label="Mentioned pathway",
    )
    main = ax.bar(
        x + width / 2,
        df["main_paper_count"],
        width=width,
        color=main_color,
        edgecolor="#374151",
        linewidth=0.35,
        label="Main pathway",
    )

    annotate_bars(ax, mentioned, total)
    annotate_bars(ax, main, total)

    ax.set_xticks(x)
    ax.set_xticklabels(df["pathway_label"])
    ax.set_ylabel("Number of papers")
    ax.set_ylim(0, max(df["mentioned_paper_count"].max(), df["main_paper_count"].max()) + 2.0)
    ax.set_title("CO$_2$/CO electroreduction to ethanol: pathway distribution", loc="left", pad=8)
    ax.grid(axis="y", color="#D9DEE7", linewidth=0.55, alpha=0.85)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", ncol=2, handlelength=1.2, columnspacing=1.2)

    note = (
        f"Counted by paper; n = {total} included papers. "
        "Mentioned and main pathways are reported separately."
    )
    ax.text(
        0,
        -0.30,
        note,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.2,
        color="#4B5563",
    )

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    fig.savefig(OUTPUT_PATH, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG figure -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
