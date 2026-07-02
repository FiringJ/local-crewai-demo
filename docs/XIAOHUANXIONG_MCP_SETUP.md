# 办公小浣熊 · 飞书闭环接入指南（Skill 为主，MCP 备用）

> 让小浣熊桌面端定时任务真正触发本地三层 skill 飞书闭环。

---

## 一、依赖验证（2026-07-03 实机核实）

| 项 | 结果 | 说明 |
| --- | --- | --- |
| LLM · SenseChat | 未配置 | `SENSENOVA_API_KEY` 为空，暂不可用 |
| LLM · DeepSeek | **可用** | `DEEPSEEK_API_KEY` 已配置，闭环 `rules_agent` 默认使用 |
| 小浣熊本地 Agent 工作区 | **已指向本项目** | `localAgentWorkspaceDir=/Users/firingj/Projects/local_crewai_demo`，且文件权限已授权本目录 |
| 小浣熊 Skill 入口 | **支持** | 技能页有「添加技能」「快速新建 Skill」（v0.7.71 实测） |
| 小浣熊 MCP 连接器 | **本版本无入口** | 设置/插件/数据源均无 MCP 配置项；MCP server 代码保留，待后续版本开放 |
| 飞书 CLI | **已连接** | 小浣熊「连接数据源」页显示飞书 CLI v1.0.56 连接成功 + 25 个 lark-* Skills |

---

## 一·五、推荐路径：Skill 接入（当前版本可用）

Skill 包：[`skills/contract-review-loop/SKILL.md`](../skills/contract-review-loop/SKILL.md)

1. 打开小浣熊桌面端 → 左侧「技能」→ **「快速新建 Skill」**（或「添加技能」→ 本地导入）。
2. 名称填 `contract-review-loop`，把上述 SKILL.md 的内容整体粘贴进去保存（若支持目录导入，直接选择 `skills/contract-review-loop/`）。
3. 小浣熊本地 Agent 工作区已是本项目根目录，Skill 里的 `uv run python scripts/...` 命令可直接执行，无需改路径。
4. 对话测试：「使用 contract-review-loop 跑一次合同审查闭环」——应看到脚本输出（当前无新合同则显示已处理 2 份）。
5. 定时任务（每天 09:00）内容直接写：

```
使用 contract-review-loop 技能执行每日合同审查闭环：
先审核飞书知识库新增合同，再对待尽调主体联网检索并写回主体画像，最后汇总汇报。
以脚本输出为准，不要编造。
```

Skill 内部编排：`feishu_contract_loop.py`（审核+写回）→ `--pending-dd`（待尽调清单）→ 小浣熊联网检索 → `--write-dd`（尽调结论回填画像）。与 MCP 方案能力完全等价，只是调用方式从 MCP 工具改为 CLI。

---

## 二、MCP Server 工具（备用：待桌面端开放 MCP 入口后启用）

脚本：[`scripts/feishu_loop_mcp_server.py`](../scripts/feishu_loop_mcp_server.py)

| 工具名 | 作用 |
| --- | --- |
| `run_feishu_loop` | 单次轮询 → 审核 → 写回报告 + 多维表格 + 主体画像（审核历史）；返回待尽调主体清单 |
| `get_pending_due_diligence` | 列出待联网尽调的乙方主体 |
| `write_due_diligence` | 把小浣熊联网检索的尽调结论写回主体画像文档 |
| `audit_contract_text` | 审核粘贴的合同正文（不读写飞书） |
| `list_feishu_wiki_nodes` | 列出知识库节点（配置确认用） |

### 编排角色分工（为什么这样设计）

- **本地 skill 做精确的事**：PDF 结构化、26 项规则计算、LLM 复核、飞书写回——这些要么零 token 要么需要 lark-cli 凭证，云端小浣熊够不到。
- **小浣熊做联网的事**：本地无搜索 API key，而小浣熊桌面端原生有联网检索。尽调由小浣熊完成后经 `write_due_diligence` 写回画像——各用所长，无降级。

---

## 三、小浣熊 MCP 连接器配置

1. 打开 **办公小浣熊桌面端 2.0** → **设置** → **MCP 连接器** → **添加连接器**
2. 类型选 **stdio**（或「命令行启动」）
3. 填写：

| 字段 | 值 |
| --- | --- |
| 名称 | `feishu-contract-loop` |
| 命令 | `uv` |
| 参数 | `run` `python` `scripts/feishu_loop_mcp_server.py` |
| 工作目录 | `/Users/firingj/Projects/local_crewai_demo` |

> 若 `uv` 不在 PATH，改用绝对路径，例如 `/Users/firingj/.local/bin/uv`。

4. 保存后，在对话中测试：「请调用 run_feishu_loop 执行一次飞书合同审核闭环」

---

## 四、定时任务 Prompt（MCP 模式用；Skill 模式见「一·五」）

在桌面端 **定时任务**（每天 09:00）中使用：

```
你是企业合同审查运营 Agent。每个工作日执行：

1. 调用 MCP 工具 run_feishu_loop，轮询飞书知识库「合同审查闭环demo」新增合同。
   本地三层 skill 会自动完成审核，并把报告写回 wiki、记录入多维表格、
   审核历史写入主体画像。
2. 检查返回 JSON 的 pending_due_diligence 字段（或调用 get_pending_due_diligence）。
3. 对每个待尽调主体，用你的联网检索能力查询：工商注册状态、经营异常、
   失信被执行、涉诉、负面舆情。每条结论必须附来源链接；查不到就如实写
   「查无」，不得编造。
4. 把尽调结论整理成 Markdown（分「工商状态 / 失信涉诉 / 尽调结论」三节），
   调用 write_due_diligence(counterparty, findings_md) 写回该主体画像。
5. 汇总汇报：处理份数、高风险数、报告链接、画像更新情况。
   若无新增合同且无待尽调主体：回复「今日无新增待审合同」。

不要编造；以工具返回 JSON 为准。
```

---

## 五、其他 Fallback

### A · Cursor 侧 Skill

[`.cursor/skills/feishu-contract-loop/SKILL.md`](../.cursor/skills/feishu-contract-loop/SKILL.md)（供 Cursor Agent 使用，与小浣熊 Skill 内容一致）。

### B · HTTP Webhook

启动审核台后 POST 触发：

```bash
uv run crew_gui --port 8765
curl -X POST http://127.0.0.1:8765/api/feishu-loop
```

---

## 六、环境变量

在 [`.env`](../.env) 中：

```bash
FEISHU_WIKI_SPACE_ID=7657968260024913086
FEISHU_BITABLE_APP=TKEdbShCyaWqa4sAnoVc9FG5nbg
FEISHU_BITABLE_TABLE=tblqAZavMQaIZUR9
FEISHU_LOOP_REVIEW_MODE=rules_agent
FEISHU_LOOP_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
```
