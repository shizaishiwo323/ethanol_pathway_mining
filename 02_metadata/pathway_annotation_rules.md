# Pathway Annotation Rules

This file defines the first-pass pathway annotation rules for ethanol formation in electrochemical CO2/CO reduction literature.

## Pathway Codes

| pathway_code | pathway_name | Chinese_name | key_intermediate | core_definition |
| --- | --- | --- | --- | --- |
| P1 | *CO dimerization pathway | *CO 二聚路径 | *OCCO / *COCO | 两个吸附态 *CO 直接发生 C-C 偶联 |
| P2 | CO-CHO coupling pathway | CO-CHO 偶联路径 | *CO-*CHO / *CHO | *CO 与加氢后的 *CHO 偶联 |
| P3 | CO-COH coupling pathway | CO-COH 偶联路径 | *CO-*COH / *COH | *CO 与 *COH 偶联 |
| P4 | CO-CHx coupling pathway | CO-CHx 偶联路径 | *CHx / *CH2 / *CH3 | *CO 与深度加氢碳中间体偶联 |
| P5 | OCHO/formate pathway | OCHO/formate 路径 | *OCHO / HCOO* / formate | *OCHO 或 formate 相关路径 |
| P6 | mixed/unclear pathway | 混合或未明确路径 | multiple / unclear | 多路径共存或文献没有明确主路径 |

## Inclusion Rules

### P1: *CO dimerization pathway

如果文献明确提出两个 *CO 直接偶联形成 *OCCO 或 *COCO，则标为 P1。

### P2: CO-CHO coupling pathway

如果文献明确提出 *CO 与 *CHO 偶联，则标为 P2。

### P3: CO-COH coupling pathway

如果文献明确提出 *CO 与 *COH 偶联，则标为 P3。

### P4: CO-CHx coupling pathway

如果文献明确提出 *CO 与 *CHx、*CH2 或 *CH3 偶联，则标为 P4。

### P5: OCHO/formate pathway

如果文献明确将 *OCHO、HCOO* 或 formate 与乙醇/C2 oxygenates 生成联系起来，则标为 P5。

### P6: mixed/unclear pathway

如果文献同时讨论多条路径但没有明确主路径，或者机制描述不清楚，则标为 P6。

## Role Definition

| role | definition |
| --- | --- |
| mention | 文献只是提及该路径 |
| main | 文献将该路径作为主要机制结论 |
| compare | 文献比较多条路径，但未明确支持其中一条 |
| reject | 文献明确排除该路径 |
| unclear | 无法判断 |

## Review Notes

- 自动匹配结果只能作为候选标签，不能直接等同于人工确认。
- 人工复核时必须区分 `manual_pathway` 和 `role`。
- 统计主路径频次时只计入 `role = main` 的人工复核结果。
