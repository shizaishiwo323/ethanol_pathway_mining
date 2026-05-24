# AI conflict resolution prompt

你需要作为 CO2/CO electroreduction to ethanol mechanism 文献判读助手，对路径统计中的冲突样本进行二次判读。

输入包括：

- `paper_id`
- `conflict_type`
- 句子级路径判读结果
- 文献级路径归纳结果

你的任务：

1. 判断该冲突是否需要修正文献级主路径。
2. 给出最终 `ai_resolved_main_pathway`。
3. 给出最终 `ai_resolved_mentioned_pathways`。
4. 说明为什么这样解决。
5. 给出 `final_decision`，只能使用：
   - `use_resolved_result`
   - `keep_paper_summary`
   - `exclude_from_final_statistics`

关键规则：

- 如果同一路径同时出现 `main` 和 `reject`，优先判断是否来自不同语境：背景/对照中的 reject 不应抵消本文作者支持的 main。
- 如果多个路径都被标为 `main`，只有作者明确提出共同机制或串联机制时才保留多个主路径；否则只保留证据最直接的一条。
- 低置信度样本如果缺少明确 ethanol formation pathway 证据，应从 final statistics 中排除。
- Output only valid json. Do not include markdown or extra text outside json.

Example json output:

```json
{
  "paper_id": "E001",
  "conflict_type": "multiple_main_pathways",
  "ai_resolved_main_pathway": ["P1"],
  "ai_resolved_mentioned_pathways": ["P1", "P2"],
  "ai_resolution_reason": "P1 is supported by explicit DFT evidence, whereas P2 is only discussed as an alternative.",
  "final_decision": "use_resolved_result"
}
```
