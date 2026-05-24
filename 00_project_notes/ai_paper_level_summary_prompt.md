# AI paper-level pathway summary prompt

你需要基于同一篇文献的所有句子级 AI 判读结果，给出文献级路径归纳。

输入字段包括：

- `paper_id`
- `sentence`
- `ai_final_pathway`
- `ai_role`
- `ai_ethanol_specific`
- `ai_evidence_type`
- `ai_evidence_reason`
- `ai_confidence`
- `ai_include_in_statistics`

文献级判断规则：

1. `final_mentioned_pathways`：汇总 `ai_role = mention / main / compare` 且 `ai_include_in_statistics = yes` 的路径。
2. `final_main_pathways`：只汇总 `ai_role = main` 且 `ai_include_in_statistics = yes` 的路径。
3. `final_rejected_pathways`：汇总 `ai_role = reject` 的路径。
4. `ethanol_specific_level`：
   - `yes`: 主证据明确指向 ethanol formation。
   - `partial`: 有 ethanol 相关证据，但也混有 C2+ oxygenates 泛化表述。
   - `unclear`: 主要是 C2+ 或机制泛述，不能确认 ethanol。
   - `no`: 与 ethanol 形成路径无关。
5. 如果句子级 main 和文献级整体证据冲突，保留冲突标记，不要强行合并。

输出字段：

| 字段 | 含义 |
| --- | --- |
| `paper_id` | 文献编号 |
| `final_mentioned_pathways` | 最终提及路径 |
| `final_main_pathways` | 最终主路径 |
| `final_rejected_pathways` | 最终排除路径 |
| `ethanol_specific_level` | `yes` / `partial` / `unclear` / `no` |
| `main_evidence_basis` | `DFT` / `spectroscopy` / `isotope` / `product distribution` / `review` / `mixed` / `unknown` |
| `ai_paper_reason` | 文献级路径判断理由 |
| `ai_paper_confidence` | `high` / `medium` / `low` |
| `final_include` | `yes` / `no` |
