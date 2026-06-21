# 合同初审周报 PPT 大纲

> 由 **办公小浣熊 · PPT 生成** 使用。每周五 17:00 定时任务汇总本周审核数据后，将本大纲粘贴至小浣熊 PPT 生成。  
> 占位符 `{...}` 由数据分析步骤输出替换。

---

## 粘贴至小浣熊 PPT 的 Prompt

```
请把以下「合同初审周报」大纲生成 6 页商务风格 PPT：
主色深蓝 + 铜色点缀，每页不超过 5 个要点，数据页建议配简单图表。
```

---

## 第 1 页 · 封面

- 标题：合同初审周报 · 第 {week_number} 周（{date_range}）
- 副标题：办公小浣熊持续运营工作流 · 合规通过率 {weekly_pass_rate}%
- 汇报对象：采购委员会 / 法务负责人
- 编制：合同初审 OPC 工作台（定时任务自动生成）

---

## 第 2 页 · 本周工作概览

- 本周待审合同：**{contract_count}** 份（较上周 {wow_change}%）
- 已完成初审：**{reviewed_count}** 份，平均耗时 **{avg_minutes}** 分钟/份（人工基准 4 小时）
- 高风险合同：**{high_risk_count}** 份，已推送法务复核
- 联网主体尽调：**{dd_count}** 次，新增观察名单主体 **{watchlist_new}** 家
- 知识库更新：风险案例 **+{case_added}** 条，法规红线 **{policy_updates}** 处

---

## 第 3 页 · 合规趋势（数据分析）

- 本周整体通过率：**{weekly_pass_rate}%**（上周 {last_week_pass_rate}%）
- 三组规则通过率：财务 **{finance_rate}%** · 法务 **{legal_rate}%** · 文本 **{text_rate}%**
- 不通过项分布：高风险 **{high_fail}** · 中风险 **{medium_fail}** · 低风险 **{low_fail}**
- 效率：累计节省人工约 **{hours_saved}** 小时（按 4h/份 × 完成数 − 实际耗时）
- 洞察 1：{insight_1}
- 洞察 2：{insight_2}

---

## 第 4 页 · Top 5 高频风险条款

1. **{top1_rule}** — 出现 {top1_count} 次 · 典型：{top1_example}
2. **{top2_rule}** — 出现 {top2_count} 次
3. **{top3_rule}** — 出现 {top3_count} 次
4. **{top4_rule}** — 出现 {top4_count} 次
5. **{top5_rule}** — 出现 {top5_count} 次

- 建议：优先修订付款比例、争议解决、税率三类条款模板

---

## 第 5 页 · 对方主体风险（联网尽调）

- 本周尽调主体：**{dd_count}** 家
- 高风险主体：**{high_risk_parties}**（已写入「对方主体画像库」）
- 新增观察名单：**{watchlist_parties}**
- 典型风险：{typical_risk_summary}
- 建议：高风险主体合同须「附条件签署」或「修订后复审」

---

## 第 6 页 · 下周行动与决策建议

- **法务**：跟进 {high_risk_count} 份高风险合同修订闭环
- **采购**：更新 {top1_rule} 相关标准合同模板
- **合规**：确认本周法规巡检结果已同步知识库红线
- **系统**：继续运行每日 09:00 / 周五 17:00 定时任务
- **决策**：本周整体建议 — **{overall_decision}**（通过 / 修订后复审 / 暂停签署）

---

## 附录 · 示例数据（Demo 单份可替换为周报汇总）

若仅有一份样本 `realistic_software_service_contract.txt` 的审核结果，可先用以下示例占位提交 PPT：

| 占位符 | 示例值 |
| --- | --- |
| week_number | 25 |
| date_range | 2026-06-16 ~ 2026-06-20 |
| weekly_pass_rate | 59 |
| contract_count | 5 |
| reviewed_count | 5 |
| avg_minutes | 3 |
| high_risk_count | 2 |
| top1_rule | 付款比例合计 |
| hours_saved | 19.75 |

完整工作流与截图要求见 [`OPC_SUBMISSION.md`](OPC_SUBMISSION.md)、[`SCREENSHOT_CHECKLIST.md`](SCREENSHOT_CHECKLIST.md)。
