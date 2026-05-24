# Codex Analysis Instruction

This project uses Python scripts for PDF-to-text conversion, candidate sentence extraction, and rule-based semantic pre-filtering.

Codex is responsible for high-level semantic analysis in the next stage.

## Input Files

Use these files in order:

1. `04_extract_results/ai_mechanism_sentence_candidates.xlsx` as the priority input.
2. `04_extract_results/ai_mechanism_sentence_labeled_all.xlsx` as the full reference input.
3. `03_text/*.txt` when broader paragraph or page context is needed.
4. `02_metadata/ai_sentence_filter_prompt.md` as the semantic screening rubric.

## Codex Task

For each candidate sentence, judge:

1. Whether it is truly relevant to ethanol formation mechanism.
2. Whether it is ethanol-specific or only C2+/oxygenate-related.
3. Whether it discusses a reaction pathway, intermediate, mechanism evidence, product performance, or background.
4. Whether the previous and next sentence are sufficient.
5. Whether broader paragraph or page context is needed.

## Output Expectations

Keep evidence traceable with:

- `paper_id`
- `txt_name`
- `page`
- `previous_sentence`
- `sentence`
- `next_sentence`
- semantic judgment fields
- concise rationale

## Do Not Do At This Stage

- Do not classify P1-P6 yet.
- Do not count pathway frequency yet.
- Do not draw pathway figures yet.
- Do not turn rule-based pre-filter labels into final mechanism conclusions.
