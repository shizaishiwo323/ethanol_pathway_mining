from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "04_extract_results" / "pathway_frequency_summary.xlsx"
OUTPUT_PATH = ROOT / "06_figures" / "pathway_sankey.html"


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    labels = ["Mentioned", "Main"] + df["pathway_code"].tolist()
    label_index = {label: index for index, label in enumerate(labels)}
    source = []
    target = []
    value = []

    for _, row in df.iterrows():
        code = row["pathway_code"]
        mentioned_count = int(row["mentioned_count"])
        main_count = int(row["main_count"])
        if mentioned_count > 0:
            source.append(label_index["Mentioned"])
            target.append(label_index[code])
            value.append(mentioned_count)
        if main_count > 0:
            source.append(label_index[code])
            target.append(label_index["Main"])
            value.append(main_count)

    fig = go.Figure(
        data=[
            go.Sankey(
                node={"label": labels, "pad": 18, "thickness": 16},
                link={"source": source, "target": target, "value": value},
            )
        ]
    )
    fig.update_layout(title_text="Ethanol Formation Pathway Distribution", font_size=12)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    fig.write_html(OUTPUT_PATH)
    print(f"Sankey figure -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
