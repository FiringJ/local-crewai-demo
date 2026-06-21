---
title: 办公小浣熊合同初审
emoji: 🦝
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
---

# 办公小浣熊 · 企业合同初审持续运营工作流

> **商汤小浣熊 OPC 高手创造赛**参赛作品：用办公小浣熊把合同初审从“人工逐份盯单”，改造成每天自动初审、每周自动复盘的持续工作流。

## 提交材料入口

| 材料 | 位置 | 作用 |
| --- | --- | --- |
| 提交说明 | [`docs/OPC_SUBMISSION.md`](docs/OPC_SUBMISSION.md) | 作品简介、完整工作流、价值和材料说明 |
| 演示文稿 | `outputs/opc-demo/ppt/opc-xiaohuanxiong-workflow-submission.pptx` | 给评委看的产品介绍 |
| 小浣熊运行录屏 | `outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/desktop-raccoon-task-run-verified.mov` | 证明任务已创建并运行过 |
| 截图包说明 | `outputs/xiaohuanxiong-screenshot-pack/MANIFEST.md` | 对每张小浣熊截图做解释 |
| 规则证据图示 | [`docs/CREWAI_RULE_EVIDENCE_FLOW.md`](docs/CREWAI_RULE_EVIDENCE_FLOW.md) | 解释合同正文、固定检查和小浣熊的关系 |

## 作品主线

| 流水线 | 触发 | 目标 |
| --- | --- | --- |
| **每日** | 工作日 09:00 · 小浣熊定时任务 | 拉取待审合同 → 逐份初审 → 高风险推送法务 |
| **每周** | 周五 17:00 · 小浣熊定时任务 | 政策更新检查 → 数据分析 → 自动生成周报演示文稿 |

完整工作流、能力地图与截图清单：

- [`docs/OPC_SUBMISSION.md`](docs/OPC_SUBMISSION.md) — 参赛主文档
- [`docs/SCREENSHOT_CHECKLIST.md`](docs/SCREENSHOT_CHECKLIST.md) — 网页端截图证据
- [`docs/WEEKLY_BRIEFING_PPT.md`](docs/WEEKLY_BRIEFING_PPT.md) — 周报演示文稿大纲
- [`prompts/xiaohuanxiong_core_prompts.md`](prompts/xiaohuanxiong_core_prompts.md) — 可复用指令

## 小浣熊六大主能力

| 能力 | 在工作流中的角色 |
| --- | --- |
| **定时任务** | 每日拉合同、每周法规巡检 + 周报 |
| **对话协作** | 逐份调度读取、查询、复核、检查、报告与归档 |
| **联网检索** | 查询乙方公开风险 + 政策和税率周检查 |
| **知识库** | 读取法务红线和历史画像；写入主体画像、风险案例、红线补丁 |
| **数据分析** | 单份合规率和风险分布；周趋势、高频风险、主体分布 |
| **演示文稿** | 单份管理层大纲 + 每周合同初审周报 |

文档处理和报告撰写是每日链路中的执行节点；本地 **固定检查清单** 只提供可复查证据，风险解释和汇报由小浣熊完成。

## 量化成效

- 单份审核：**4 小时 → 3 分钟**（约 **92%** 节省）
- 规则覆盖：**固定检查清单**（当前 26 项 / 6 组，见 `knowledge/contract_audit_rules.md`）
- 周报：人工 **约 2 小时 → 约 10 分钟**（定时任务 + 小浣熊生成演示文稿）

---

## 本仓库可体验部分的定位

`uv run crew_gui` 启动的是工作流中的 **审核引擎节点**（对应每日流水线步骤 3–8）：

```
读取合同 → 固定检查 → 知识库依据 → 数据分析 → 审核报告 → 汇报大纲
```

用于评委 **可体验验证** 单份合同从读取到出报告的过程；**定时任务、联网查询、知识库存取、周报演示文稿** 在小浣熊端按截图清单复现。

---

## 运行

### 启动 GUI

```bash
uv run crew_gui --no-open
```

打开终端输出的本地地址，上传 `knowledge/realistic_software_service_contract.txt` 后点击「开始审核」。

### 前端（React + shadcn/ui）

```bash
cd frontend && npm install && npm run build
```

开发模式：

```bash
# 终端 1
uv run crew_gui --no-open --port 7860

# 终端 2
cd frontend && npm run dev
```

### 命令行

```bash
uv run run_crew knowledge/sample_contract.txt
```

## 审核模式

- **小浣熊全链路（推荐）**：规则证据 → 知识库 → 数据分析 → SenseChat 报告 + 汇报大纲（需 `SENSENOVA_API_KEY`）
- **仅规则引擎（离线演示）**：不调用 LLM，仍可输出规则报告、数据洞察、汇报模板

## LLM 配置（办公小浣熊 / SenseNova）

```bash
SENSENOVA_API_KEY=你的商汤API密钥
MODEL=openai/SenseChat-5
BASE_URL=https://api.sensenova.cn/compatible-mode/v2

# 可选：Demo 启用小浣熊原生联网（与工作流「主体尽调」一致）
SENSENOVA_SEARCH_ENABLE=true
```

详见 [`.env.example`](.env.example)。密钥可在 [商汤大装置](https://www.sensecore.cn) 或赛事 API Key 任务页获取。

## 测试合同样本

- `knowledge/sample_contract.txt` — 演示采购合同
- `knowledge/realistic_software_service_contract.txt` — 软件服务合同（含争议解决等问题）
- `knowledge/contract_audit_kb.md` — 法务红线（上传至小浣熊知识库）

## 规则覆盖（证据层）

- 财务条款：12 条 · 法务合规：7 条 · 文本质量：3 条  
- 实现：[`src/local_crewai_demo/contract_review.py`](src/local_crewai_demo/contract_review.py)

## 云端部署

见 [`docs/DEPLOY_NO_CARD.md`](docs/DEPLOY_NO_CARD.md)（Hugging Face Spaces / Cloudflare 隧道）。

```bash
docker build -t contract-audit .
docker run --rm -p 7860:7860 -e PORT=7860 -e SENSENOVA_API_KEY=你的key contract-audit
```
