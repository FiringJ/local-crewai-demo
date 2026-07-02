---
name: feishu-contract-loop
description: 触发飞书知识库合同审核闭环（三层 skill + 写回 wiki + 多维表格）。当用户要求跑飞书闭环、审核知识库新合同、或 MCP 不可用时执行本地脚本。
---

# 飞书合同审核闭环 Skill

## 何时使用

- 用户说「跑飞书闭环」「审核知识库新合同」「执行 feishu_contract_loop」
- 小浣熊 MCP 连接器未配置时的 fallback
- 定时任务需触发本地三层 skill 审核节点

## 执行命令

在项目根目录执行（**必须**）：

```bash
cd /Users/firingj/Projects/local_crewai_demo && uv run python scripts/feishu_contract_loop.py
```

仅列出知识库节点（配置确认）：

```bash
uv run python scripts/feishu_contract_loop.py --list-nodes
```

Dry-run（不实际审核）：

```bash
uv run python scripts/feishu_contract_loop.py --dry-run
```

## 前置条件

- `lark-cli` 已 auth（`lark-cli auth status`）
- `.env` 已配置 `FEISHU_WIKI_SPACE_ID`、`FEISHU_BITABLE_APP`、`FEISHU_BITABLE_TABLE`
- `rules_agent` 模式需 `DEEPSEEK_API_KEY` 或 `SENSENOVA_API_KEY`

## 输出说明

脚本 stdout 会打印：待审份数、审核进度、报告 wiki URL、多维表格写入结果。  
向用户汇报时引用工具输出，不要编造链接或数字。

## MCP 优先

若已配置 MCP 连接器（见 `docs/XIAOHUANXIONG_MCP_SETUP.md`），优先调用工具 `run_feishu_loop`，勿重复跑脚本。
