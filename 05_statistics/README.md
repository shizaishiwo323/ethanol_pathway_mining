# Stage 4-6 Statistics Outputs

This directory stores paper-level pathway summaries, conflict checks, and final pathway frequency tables.

## `paper_level_pathway_summary.xlsx`

Aggregates sentence-level AI review results by `paper_id`. One paper counts once per pathway, regardless of how many sentences mention that pathway.

Key columns:

- `mentioned_pathways`: pathways with included `mention`, `main`, or `compare` sentence-level roles.
- `main_pathways`: pathways with included `main` sentence-level roles.
- `compared_pathways`: pathways compared without a single supported route.
- `rejected_pathways`: pathways explicitly rejected or described as unfavorable.
- `ethanol_specific_pathways`: included pathways explicitly connected to ethanol.

## `paper_level_ai_summary.xlsx`

Condensed paper-level AI summary used by `scripts/07_calculate_pathway_frequency.py`.

## `pathway_conflict_report.xlsx`

Flags cases requiring second-pass review, including:

- multiple pathways assigned as `main` within one paper;
- the same pathway appearing as both `main` and `reject`;
- low-confidence sentence-level decisions included in statistics.

## `pathway_conflict_ai_resolved.xlsx`

Resolution template for second-pass AI review. If `final_decision` is filled, `scripts/07_calculate_pathway_frequency.py` uses the non-empty resolved pathway fields to update the final counts.

## `pathway_frequency_summary.xlsx`

Final coarse/fine distribution table by paper count. `mentioned_paper_count` is the coarse distribution, and `main_paper_count` is the fine main-mechanism distribution.
