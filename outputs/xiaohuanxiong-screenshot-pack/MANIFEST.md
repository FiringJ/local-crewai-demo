# 小浣熊截图证据包清单

本清单用于说明每张截图在提交材料中证明什么。建议评委按“看入口、看任务、看运行、看结果、看沉淀、看周报”的顺序理解作品。

---

## 最建议放入演示文稿的截图

| 优先级 | 截图 | 证明点 |
| --- | --- | --- |
| 1 | `11-desktop-app/01-desktop-home-local-agent.png` | 小浣熊桌面端已登录，能看到本地协作、技能、记忆中心、数据源、定时任务入口 |
| 2 | `11-desktop-app/04-schedule-create-filled.png` | 定时任务创建表单已填写，包含每天 09:00 合同初审流水线 |
| 3 | `11-desktop-app/05-schedule-created-list.png` | 定时任务创建成功，进入待执行列表 |
| 4 | `12-desktop-task-run/02-task-menu-run-option.png` | 已创建任务右侧菜单含“立刻运行”，证明可手动触发 |
| 5 | `12-desktop-task-run/03-task-running-manual-trigger.png` | 任务触发后进入运行中状态 |
| 6 | `12-desktop-task-run/06-task-complete-summary-updated.png` | 任务完成后摘要被小浣熊更新 |
| 7 | `05-knowledge-write/09-knowledge-file-ingested.png` | 知识库文件已入库，证明红线和案例可沉淀 |
| 8 | `08-ppt-generation/04-ppt-outline-pages-generating.png` | 周报演示文稿生成过程截图，证明复盘闭环 |

---

## 桌面端真实操作记录

| 能力 | 已完成操作 | 证据截图 |
| --- | --- | --- |
| 定时任务 | 创建 `OPC演示-每日合同初审流水线`，调度为每天 09:00，任务内容覆盖合同读取、对方公司风险查询、知识库复核、22 项固定检查、审核报告和高风险提醒 | `11-desktop-app/02-schedule-home.png` 至 `11-desktop-app/05-schedule-created-list.png` |
| 任务运行 | 右侧更多菜单打开后出现 `立刻运行`；已手动触发过一次，页面出现运行中状态，并在完成后更新摘要 | `12-desktop-task-run/01-schedule-task-ready.png`、`12-desktop-task-run/02-task-menu-run-option.png`、`12-desktop-task-run/03-task-running-manual-trigger.png`、`12-desktop-task-run/06-task-complete-summary-updated.png` |
| 操作录屏 | 录制桌面端小浣熊任务页，包含“立刻运行”入口与任务触发过程 | `12-desktop-task-run/desktop-raccoon-task-run-verified.mov` |
| 对话协作 | 在桌面端发起“评委解释口径”请求，要求小浣熊解释合同审核工作流和规则证据关系 | `11-desktop-app/06-local-agent-prompt-workflow.png` |
| 结果说明 | 小浣熊生成合同审核执行形态说明、流程图、规则证据包、能力分工和总结 | `11-desktop-app/09-local-agent-workflow-result-mid.png`、`11-desktop-app/11-local-agent-workflow-result-final.png` |

---

## 网页端真实操作记录

| 能力 | 已完成操作 | 证据截图 |
| --- | --- | --- |
| 对话协作 | 生成企业合同初审多步骤拆解 | `02-agent-orchestration/02-agent-orchestration-report.png` |
| 文档处理 | 粘贴脱敏合同样本，完成字段抽取 | `03-document-parse/03-contract-parse-result.png` |
| 固定检查证据 | 输出 22 条固定检查映射与风险摘要 | `03-document-parse/04-contract-parse-rule-evidence-result.png` |
| 对方公司风险查询 | 发起对方公司公开风险查询请求；当前环境返回“无联网工具”降级说明 | `04-web-search-due-diligence/04-due-diligence-no-web-fallback-result.png` |
| 知识库写入 | 上传脱敏知识库 `kb.md`，状态从等待中变为已入库 | `05-knowledge-write/01-knowledge-base-entry.png` 至 `05-knowledge-write/09-knowledge-file-ingested.png` |
| 周报生成 | 生成“企业合同初审每日流水线”周报大纲和页面过程 | `08-ppt-generation/01-ppt-generation-settings.png` 至 `08-ppt-generation/05-ppt-outline-later.png` |

---

## 需要如实说明的限制

- 网页端对方公司风险查询环节中，小浣熊当前会话明确返回“没有可用的联网检索工具”，因此截图包保留真实降级结果，不能包装成已完成真实工商或司法查询。
- 桌面端已真实创建演示定时任务；任务名称带 `OPC演示`，便于后续在小浣熊里识别和删除。
- 桌面端任务已手动触发并录屏；运行中状态由 `03-task-running-manual-trigger.png` 佐证，完成状态由 `06-task-complete-summary-updated.png` 佐证。
- 本地审核台和提交演示文稿位于 `outputs/opc-demo/`，定位是“每日工作流中的合同审核节点”，不是完整小浣熊持续运营界面。

---

## 推荐讲述顺序

1. 先放 `11-desktop-app/01-desktop-home-local-agent.png`：说明这是小浣熊真实入口。
2. 放 `11-desktop-app/05-schedule-created-list.png`：证明工作流不是一次性聊天，而是定时运营。
3. 放 `12-desktop-task-run/02-task-menu-run-option.png` 和录屏：证明任务可以触发。
4. 放 `03-document-parse/04-contract-parse-rule-evidence-result.png`：解释 22 项固定检查只做可复查证据。
5. 放 `05-knowledge-write/09-knowledge-file-ingested.png`：证明知识库沉淀。
6. 放 `08-ppt-generation/04-ppt-outline-pages-generating.png`：证明管理层周报输出。
7. 最后展示本地审核台结果或提交演示文稿：证明单份合同审核节点可体验。
