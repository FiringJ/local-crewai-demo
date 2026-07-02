---
title: 办公小浣熊合同审查
emoji: 🦝
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
---

# 办公小浣熊 · 企业合同审查持续运营工作流

> **商汤小浣熊挑战赛**参赛作品：用办公小浣熊把合同审查从「人工逐份盯单」改造成每天自动审查、结果沉淀飞书、每周自动复盘的持续工作流。
>
> **参赛相关的一切（进展 / 材料 / 路演清单 / 规划）→ [`docs/COMPETITION_GUIDE.md`](docs/COMPETITION_GUIDE.md)**

## 一句话架构

```
飞书知识库(合同) ──→ 三层混合审核 ──→ 报告写回 wiki + 多维表格 + 主体画像
                    │ 1. PDF→Markdown（0 token）
                    │ 2. 规则引擎 26 项（0 token，精确计算）
                    │ 3. LLM 复核（CrewAI，A/B 实测省 25.2% token）
                    └── 小浣熊编排：定时任务 → Skill → 本地脚本 → 待尽调清单 → 小浣熊联网检索 → 回填画像
```

## 仓库结构

| 路径 | 内容 |
| --- | --- |
| `src/local_crewai_demo/` | 核心代码：`contract_review.py` 规则引擎、`pdf_markdown.py` PDF 结构化、`crew.py` CrewAI 双 Agent、`gui.py` 审核台后端 |
| `scripts/` | `feishu_contract_loop.py` 飞书闭环（含主体画像/尽调 CLI）、`feishu_loop_mcp_server.py` MCP 备用 |
| `skills/contract-review-loop/` | 小浣熊 Skill 定义（主接入方案，粘贴到小浣熊「技能」即可） |
| `knowledge/` | 样本合同、审核规则、法务红线知识库 |
| `frontend/` | React + shadcn 审核台前端 |
| `docs/` | 全部文档（索引见参赛指南第六节） |
| `prompts/` | 小浣熊可复用指令 |
| `outputs/opc-demo/` | 提交材料：PPT、附件 zip、截图、审核结果 |
| `outputs/xiaohuanxiong-screenshot-pack/` | 小浣熊界面证据包（含 MANIFEST） |
| `_archive/` | 已淘汰的过程产物（gitignore，可整体删除） |

## 快速开始

### 本地审核台（评委可体验部分）

```bash
uv run crew_gui --no-open
# 打开终端输出的地址，上传 knowledge/realistic_software_service_contract.txt，点「开始审核」
```

命令行：`uv run run_crew knowledge/sample_contract.txt`

前端开发模式：`uv run crew_gui --no-open --port 7860` + `cd frontend && npm run dev`

### 飞书闭环

```bash
# 单次轮询：检测新合同 → 审核 → 写回 wiki/多维表格/主体画像
uv run python scripts/feishu_contract_loop.py --once

# Skill 交互用：查待尽调清单 / 回填尽调结论
uv run python scripts/feishu_contract_loop.py --pending-dd
uv run python scripts/feishu_contract_loop.py --write-dd "主体名" --findings-file findings.md
```

前置：`lark-cli` 已认证（wiki/base/docs/drive 权限），`.env` 配好 `FEISHU_WIKI_SPACE_ID` / `FEISHU_BITABLE_APP` / `FEISHU_BITABLE_TABLE`。详见 [`docs/FEISHU_CLOSED_LOOP.md`](docs/FEISHU_CLOSED_LOOP.md)。

### 小浣熊接入

Skill 主方案：把 [`skills/contract-review-loop/SKILL.md`](skills/contract-review-loop/SKILL.md) 导入小浣熊「技能」。步骤与定时任务 Prompt 见 [`docs/XIAOHUANXIONG_MCP_SETUP.md`](docs/XIAOHUANXIONG_MCP_SETUP.md)。

## 审核模式与 LLM 配置

| 模式 | 说明 |
| --- | --- |
| `rules_only` | 纯规则引擎，0 token，离线可跑 |
| `rules_agent` | 规则证据 + LLM 复核报告（推荐） |

```bash
# .env（SenseChat 口径，也可用 DeepSeek 平替演示）
SENSENOVA_API_KEY=你的商汤密钥
MODEL=openai/SenseChat-5
BASE_URL=https://api.sensenova.cn/compatible-mode/v2
FEISHU_LOOP_REVIEW_MODE=rules_agent
```

详见 [`.env.example`](.env.example)。

## 实测数据（2026-07-03）

- 128 万元软件服务合同：检出 **3 项高风险**，通过率 65.4%
- 200 万元智能硬件合同：LLM 复核报告 + 多维表格记录 NO.002 写回成功
- **真实底稿合同**（政府采购网中标公告还原，57.95 万元，真实乙方主体）：3 项高风险 + 真实联网尽调写回主体画像
- **Token A/B 实测**（`scripts/token_ab_test.py`，API usage 实计）：纯 LLM 两轮 18327 vs 混合架构单轮 13705，节省 **25.2%**
- 3 份主体画像自动生成并累积审核历史与尽调结论
- 单份人工 4h → 3min 为**估算**口径（PPT 已标注）

## 云端部署

Hugging Face Spaces / Docker，见 [`docs/DEPLOY_NO_CARD.md`](docs/DEPLOY_NO_CARD.md)：

```bash
docker build -t contract-audit .
docker run --rm -p 7860:7860 -e PORT=7860 -e SENSENOVA_API_KEY=你的key contract-audit
```
