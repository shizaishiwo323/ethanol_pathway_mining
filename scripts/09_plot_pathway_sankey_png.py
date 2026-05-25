from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FREQ_PATH = ROOT / "05_statistics" / "pathway_frequency_summary.xlsx"
OUTPUT_PATH = ROOT / "06_figures" / "pathway_distribution_sankey_first_version.png"


PATHWAY_ORDER = ["P1", "P2", "P3", "P4", "P5", "P6"]
PATHWAY_LABELS = {
    "P1": "*CO dimerization",
    "P2": "CO-CHO coupling",
    "P3": "CO-COH coupling",
    "P4": "CO-CHx coupling",
    "P5": "OCHO/formate",
    "P6": "mixed/unclear",
}
PATHWAY_COLORS = {
    "P1": "#7FA1C3",
    "P2": "#D8A06A",
    "P3": "#8CBF9F",
    "P4": "#B7A0D6",
    "P5": "#D78A8A",
    "P6": "#A9A9A9",
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
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "savefig.facecolor": "white",
        }
    )


def load_data() -> pd.DataFrame:
    df = pd.read_excel(FREQ_PATH)
    df = df[df["pathway_code"].isin(PATHWAY_ORDER)].copy()
    df["pathway_code"] = pd.Categorical(df["pathway_code"], PATHWAY_ORDER, ordered=True)
    df = df.sort_values("pathway_code").reset_index(drop=True)
    df["mentioned_only_count"] = df["mentioned_paper_count"] - df["main_paper_count"]
    if (df["mentioned_only_count"] < 0).any():
        raise ValueError("main_paper_count cannot exceed mentioned_paper_count for Sankey plotting.")
    return df


def ribbon(ax, x0, x1, y0a, y0b, y1a, y1b, color, alpha=0.72, zorder=1):
    curve = 0.34 * (x1 - x0)
    path = MplPath(
        [
            (x0, y0a),
            (x0 + curve, y0a),
            (x1 - curve, y1a),
            (x1, y1a),
            (x1, y1b),
            (x1 - curve, y1b),
            (x0 + curve, y0b),
            (x0, y0b),
            (x0, y0a),
        ],
        [
            MplPath.MOVETO,
            MplPath.CURVE4,
            MplPath.CURVE4,
            MplPath.CURVE4,
            MplPath.LINETO,
            MplPath.CURVE4,
            MplPath.CURVE4,
            MplPath.CURVE4,
            MplPath.CLOSEPOLY,
        ],
    )
    ax.add_patch(PathPatch(path, facecolor=color, edgecolor="none", alpha=alpha, zorder=zorder))


def add_node(ax, x, y_bottom, height, label, facecolor, align="left", fontsize=6.2):
    width = 0.025
    ax.add_patch(
        Rectangle(
            (x - width / 2, y_bottom),
            width,
            height,
            facecolor=facecolor,
            edgecolor="#3F4652",
            linewidth=0.45,
            zorder=3,
        )
    )
    text_x = x - 0.028 if align == "right" else x + 0.028
    ha = "right" if align == "right" else "left"
    ax.text(
        text_x,
        y_bottom + height / 2,
        label,
        ha=ha,
        va="center",
        fontsize=fontsize,
        zorder=4,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.2},
    )


def stacked_positions(values, top=0.88, bottom=0.14, gap=0.018):
    total = sum(values)
    usable = top - bottom - gap * (len(values) - 1)
    scale = usable / total if total else 0
    positions = []
    y_top = top
    for value in values:
        height = value * scale
        y_bottom = y_top - height
        positions.append((y_bottom, y_top, height))
        y_top = y_bottom - gap
    return positions, scale


def main() -> None:
    setup_style()
    df = load_data()

    mentioned_total = int(df["mentioned_paper_count"].sum())
    main_total = int(df["main_paper_count"].sum())
    mentioned_only_total = int(df["mentioned_only_count"].sum())
    total_papers = int(df["total_valid_papers"].max())

    source_values = df["mentioned_paper_count"].astype(int).tolist()
    source_positions, scale = stacked_positions(source_values)
    path_positions = source_positions
    sink_values = [main_total, mentioned_only_total]
    sink_positions, _ = stacked_positions(sink_values, top=0.82, bottom=0.20, gap=0.05)

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    ax.set_xlim(0, 1.04)
    ax.set_ylim(0, 1)
    ax.axis("off")

    x_source, x_path, x_sink = 0.08, 0.50, 0.91
    source_y0, source_y1 = min(p[0] for p in source_positions), max(p[1] for p in source_positions)
    add_node(
        ax,
        x_source,
        source_y0,
        source_y1 - source_y0,
        f"Mentioned pathway-paper records\nn={mentioned_total}",
        "#E7ECF3",
        align="right",
        fontsize=6.4,
    )

    source_cursor = source_y1
    main_sink_y0, main_sink_y1, _ = sink_positions[0]
    only_sink_y0, only_sink_y1, _ = sink_positions[1]
    main_cursor = main_sink_y1
    only_cursor = only_sink_y1

    for row, (path_y0, path_y1, path_h) in zip(df.itertuples(), path_positions):
        code = str(row.pathway_code)
        mentioned = int(row.mentioned_paper_count)
        main = int(row.main_paper_count)
        mentioned_only = int(row.mentioned_only_count)
        color = PATHWAY_COLORS[code]

        source_next = source_cursor - mentioned * scale
        ribbon(ax, x_source + 0.0125, x_path - 0.0125, source_next, source_cursor, path_y0, path_y1, color, 0.55)
        source_cursor = source_next - 0.018

        add_node(
            ax,
            x_path,
            path_y0,
            path_h,
            f"{code} {PATHWAY_LABELS[code]}  {mentioned}/{main}",
            color,
            align="left",
            fontsize=5.9,
        )

        path_cursor = path_y1
        if main:
            main_next = main_cursor - main * scale
            ribbon(ax, x_path + 0.0125, x_sink - 0.0125, main_next, main_cursor, path_cursor - main * scale, path_cursor, color, 0.72)
            main_cursor = main_next
            path_cursor -= main * scale
        if mentioned_only:
            only_next = only_cursor - mentioned_only * scale
            ribbon(
                ax,
                x_path + 0.0125,
                x_sink - 0.0125,
                only_next,
                only_cursor,
                path_cursor - mentioned_only * scale,
                path_cursor,
                color,
                0.32,
            )
            only_cursor = only_next

    add_node(
        ax,
        x_sink,
        main_sink_y0,
        main_sink_y1 - main_sink_y0,
        f"Main pathway assignments\nn={main_total}",
        "#D08B73",
        align="left",
        fontsize=6.4,
    )
    add_node(
        ax,
        x_sink,
        only_sink_y0,
        only_sink_y1 - only_sink_y0,
        f"Mentioned only records\nn={mentioned_only_total}",
        "#C9D3DF",
        align="left",
        fontsize=6.4,
    )

    ax.text(
        0.02,
        0.972,
        "CO$_2$/CO electroreduction to ethanol: first pathway Sankey",
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
    )
    ax.text(
        x_path + 0.028,
        0.905,
        "Pathway labels show mentioned/main records",
        ha="left",
        va="center",
        fontsize=5.8,
        color="#4B5563",
    )
    ax.text(
        0.02,
        0.055,
        f"Final statistics table; n = {total_papers} included papers. "
        "One paper may contribute more than one pathway-paper record.",
        ha="left",
        va="bottom",
        fontsize=6.4,
        color="#4B5563",
    )

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    fig.savefig(OUTPUT_PATH, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG Sankey figure -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
