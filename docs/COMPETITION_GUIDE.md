# 参赛指南 · 商汤小浣熊挑战赛（赛道二）

> 本文是参赛工作的单一入口：当前进展、已实现功能、材料索引、路演清单、未来规划。
> 技术细节见各专项文档（文末索引）。

**作品**：办公小浣熊 · 企业合同审查持续运营工作流
**阶段**：初赛已通过 → 复赛表单已提交 → 备战周六路演（Demo Day）

---

## 一、当前进展

| 时间 | 事项 | 状态 |
| --- | --- | --- |
| 初赛 | 合同初审工作流（PPT 8 页 + 录屏 + 截图包 + 附件 zip） | 已通过 |
| 2026-07-02 晚 | 复赛表单提交（作品简介按「合同审查 + 三层 skill + 飞书闭环」口径） | 已提交，内容见 `docs/复赛提交表单.md` |
| 2026-07-03 凌晨 | 复赛升级全部落地并实测（见下节） | 完成 |
| 周六 | 复赛路演 Demo Day | **待办**（见「四、路演清单」） |

### 复赛升级实测记录（2026-07-03）

- **NO.001**（rules_only）：128 万软件服务合同 → 3 项高风险、通过率 65.4%、14931 token、节省 17.6%
- **NO.002**（rules_agent + DeepSeek）：200 万智能硬件合同 → LLM 复核报告写回、通过率 69.2%
- **2 份主体画像**写回飞书 wiki（审核历史 + 联网尽调结论）
- 飞书闭环 demo：知识库 `7657968260024913086`「合同审查闭环demo」+ 多维表格 `TKEdbShCyaWqa4sAnoVc9FG5nbg`
- 全部 URL 与字段见 `docs/FEISHU_CLOSED_LOOP.md` 第八节

---

## 二、已实现功能

### 核心：三层可复用 skill（混合架构）

| 层 | 实现 | 成本 |
| --- | --- | --- |
| PDF 结构化 | `src/local_crewai_demo/pdf_markdown.py`（PyMuPDF 还原层级/表格） | 0 token |
| 规则引擎 | `src/local_crewai_demo/contract_review.py`（26 项 / 6 组，对接上位法，Decimal 精确计算） | 0 token |
| LLM 复核 | `src/local_crewai_demo/crew.py`（CrewAI 2 Agent：审核 + 汇报大纲） | 仅此层耗 token，实测节省 17.6% |

### 飞书闭环（scripts/feishu_contract_loop.py）

写入合同 → 轮询检测 → 三层审核 → **审核报告写回 wiki** → **多维表格结构化记录** → **主体画像**（审核历史自动累积 + 小浣熊联网尽调回填）。支持 `rules_only` / `rules_agent` 两模式，均已实测跑通。

### 小浣熊接入（三条通道）

| 通道 | 状态 | 说明 |
| --- | --- | --- |
| **Skill（主方案）** | 已就绪，待用户配置 | `skills/contract-review-loop/SKILL.md`，小浣熊「技能 → 快速新建 Skill」导入 |
| MCP server（备用） | 代码就绪 | `scripts/feishu_loop_mcp_server.py`（5 工具）；当前桌面端 v0.7.71 无 MCP 入口，待开放 |
| HTTP webhook（备用） | 已实现 | `POST /api/feishu-loop`（需先 `uv run crew_gui`） |

### 演示与交付物

- 本地审核台：`uv run crew_gui`（React + shadcn 前端，token 计量展示）
- 复赛 PPT 12 页（瑞士风）：`outputs/opc-demo/ppt/opc-xiaohuanxiong-workflow-submission.pptx`
- 诚实口径已全面核对：4h→3min 标注估算、22/26 差异标注、尽调「查无」如实呈现

---

## 三、材料索引（提交 / 路演用）

| 材料 | 路径 |
| --- | --- |
| 复赛表单内容底稿 | `docs/复赛提交表单.md` |
| 复赛 PPT（12 页） | `outputs/opc-demo/ppt/opc-xiaohuanxiong-workflow-submission.pptx`（预览图同目录 `xiaohuanxiong-preview/`） |
| 提交附件 zip | `outputs/opc-demo/合同初审持续运营工作流-附件-提交.zip`（录屏 / Prompt / 截图三件套） |
| 小浣熊界面证据包 | `outputs/xiaohuanxiong-screenshot-pack/`（`MANIFEST.md` 逐张解释） |
| 飞书闭环 demo 链接 | 见 `docs/FEISHU_CLOSED_LOOP.md` 第八节（wiki + 多维表格 + 画像，可现场打开） |
| 审核台截图 | `outputs/opc-demo/screenshots/` |
| 样本审核结果 JSON | `outputs/opc-demo/review-response.json` |
| 核心 Prompt | `prompts/xiaohuanxiong_core_prompts.md` |

---

## 四、路演清单（周六前待办）

1. **小浣熊配置 Skill**（约 10 分钟）：技能 → 快速新建 Skill → 粘贴 `skills/contract-review-loop/SKILL.md`；对话测试「使用 contract-review-loop 技能跑一次合同审查闭环」；把定时任务 Prompt 换成 `docs/XIAOHUANXIONG_MCP_SETUP.md`「一·五」的版本。
2. **补飞书 UI 截图**（路演证据）：wiki 双合同 + 报告、多维表格 NO.001/NO.002、两份主体画像文档。
3. **（可选）录一段新演示**：往知识库放一份新合同 → 小浣熊跑 Skill → 报告/表格/画像全链路写回。
4. **（可选）恢复 HF Space** 拿稳定访问链接（`docs/DEPLOY_NO_CARD.md`）。
5. **彩排讲述顺序**：痛点 → 三层 skill（零 token）→ 飞书闭环实测 → 小浣熊编排（Skill 双向流水线）→ 数据与价值。

### 路演答问口径（已核实）

- **「数字有没有夸大？」**：3 高风险 / 65.4% / 17.6% 为 128 万样本实测；4h→3min 为估算（PPT 已标注）；主体画像与尽调已真实实现并写回飞书。
- **「主体画像之前为什么没有？」**：初版把它放在云端 Agent Prompt 里，云端够不到企业飞书写入通道；重构后「审核历史本地写 + 尽调小浣熊查、经 Skill 回填」，详见 `docs/FEISHU_CLOSED_LOOP.md` 第四节。
- **「小浣熊怎么串起全流程？」**：定时任务 → contract-review-loop Skill → 本地三层 skill 审核写回 → 返回待尽调清单 → 小浣熊原生联网检索 → 结论回填画像。

---

## 五、未来规划

### 短期（路演后 → 决赛）

- MCP 入口开放后切换到 MCP 接入（server 已备好），演示「工具级」编排
- 接入 SenseChat（`SENSENOVA_API_KEY`），演示口径与小浣熊生态完全统一
- 周报自动化闭环：周五定时任务读多维表格 → 数据分析 → 自动生成周报 PPT（当前为大纲，升级为成品）
- HF Space 稳定访问链接，评委可自助体验

### 中长期（产品化方向）

- 合同类型矩阵扩展：T1 货物采购 / T2 技术服务 / T3 承揽安装 / T4 混合合同的差异化规则集
- 批量并发审核 + 队列，多份合同同日进入闭环
- 主体画像跨合同累积 → 供应商风险分级（画像数据已具备结构基础）
- 真实企业合同脱敏试点，验证 30-40% 的大合同 token 节省预估

---

## 六、专项文档索引

| 文档 | 内容 |
| --- | --- |
| `docs/FEISHU_CLOSED_LOOP.md` | 飞书闭环架构、主体画像卡点分析与重构、实证记录（URL/字段全量） |
| `docs/XIAOHUANXIONG_MCP_SETUP.md` | 小浣熊接入指南（Skill 主方案 + MCP 备用 + 定时任务 Prompt） |
| `docs/TECH_SKILL_ARCHITECTURE.md` | 三层 skill 设计与 token 成本量化 |
| `docs/复赛提交表单.md` | 复赛表单全部字段底稿 |
| `docs/OPC_SUBMISSION.md` | 初赛主文档（工作流全景 + 如实说明） |
| `docs/CREWAI_RULE_EVIDENCE_FLOW.md` | 规则证据与小浣熊的关系图示 |
| `docs/WEEKLY_BRIEFING_PPT.md` | 周报演示文稿大纲 |
| `docs/SCREENSHOT_CHECKLIST.md` | 截图证据清单 |
| `docs/DEPLOY.md` / `docs/DEPLOY_NO_CARD.md` | 云端部署（Docker / HF Spaces） |
