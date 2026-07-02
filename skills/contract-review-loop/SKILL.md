---
name: contract-review-loop
description: 企业合同审查飞书闭环。轮询飞书知识库新增合同，本地三层 skill（PDF结构化·26项规则引擎·LLM复核）审核后，把审核报告、多维表格记录、主体画像写回飞书；再对乙方主体联网尽调并回填画像。当用户或定时任务提到「合同审查」「审核新合同」「跑闭环」「尽调」时使用。
---

# 合同审查飞书闭环 Skill

本 Skill 通过执行本地脚本驱动完整闭环。工作目录即本工作区根目录（`/Users/firingj/Projects/local_crewai_demo`）。

## 完整编排（定时任务 / 用户要求跑闭环时按顺序执行）

### 第 1 步 · 审核新合同

```bash
uv run python scripts/feishu_contract_loop.py
```

脚本会自动：检测飞书知识库「合同审查闭环demo」新增合同 → 三层 skill 审核 →
审核报告写回 wiki → 结构化记录写入多维表格 → 主体画像（审核历史）写回。
输出末尾的 JSON 含 `pending_due_diligence`（待尽调主体清单）。

### 第 2 步 · 查看待尽调主体

```bash
uv run python scripts/feishu_contract_loop.py --pending-dd
```

返回 JSON：`pending[].counterparty`（主体名）、`contracts`（关联合同）、`profile_url`（画像文档）。
若 `count` 为 0，跳到第 4 步。

### 第 3 步 · 联网尽调并写回画像

对每个待尽调主体：

1. 用你的联网检索能力查询该主体的：工商注册状态、经营异常、失信被执行、涉诉、负面舆情。
2. 整理成 Markdown，分三节：`### 工商状态`、`### 失信 / 涉诉 / 负面信息`、`### 尽调结论`。
   每条结论必须附来源链接；查不到就如实写「查无」，**不得编造**。
3. 把 Markdown 存为临时文件（如 `/tmp/dd-<主体名>.md`），然后写回：

```bash
uv run python scripts/feishu_contract_loop.py --write-dd "<主体名>" --findings-file /tmp/dd-<主体名>.md
```

成功时返回 `{"ok": true, "profile_url": ...}`，尽调结论已合并进飞书画像文档。

### 第 4 步 · 汇总汇报

向用户汇报：处理合同份数、高风险数、报告链接、画像更新情况（引用脚本输出的真实链接与数字，不要编造）。
若无新增合同且无待尽调主体，回复「今日无新增待审合同」。

## 辅助命令

| 用途 | 命令 |
| --- | --- |
| 仅列知识库节点 | `uv run python scripts/feishu_contract_loop.py --list-nodes` |
| Dry-run（不审核不写回） | `uv run python scripts/feishu_contract_loop.py --dry-run` |
| 审核粘贴的合同文本 | 见 `scripts/feishu_loop_mcp_server.py` 的 `audit_contract_text`（或让用户用本地审核台） |

## 前置条件（异常时提示用户）

- 飞书 CLI 已连接（本机 lark-cli 已 auth，数据源页显示「连接成功」即可）
- `.env` 已配置 `FEISHU_WIKI_SPACE_ID` / `FEISHU_BITABLE_APP` / `FEISHU_BITABLE_TABLE` / `DEEPSEEK_API_KEY`
- 若脚本报「lark-cli 失败 … scope」类错误：提示用户运行 `lark-cli auth login --domain wiki,base,docs,drive --no-wait --json` 重新授权
