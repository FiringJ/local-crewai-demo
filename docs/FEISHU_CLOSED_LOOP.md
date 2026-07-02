# 飞书知识库合同审核闭环

> 回应导师反馈二：打通飞书工具生态。当文档写入飞书知识库时自动触发合同审核，结果沉淀回知识库，跑通完整闭环。

---

## 一、闭环架构

```
        ┌──────────────────────────────────────────────┐
        │            飞书知识库（合同目录）              │
        │  用户写入 / 上传新合同文档（docx）             │
        └───────────────┬──────────────────────────────┘
                        │ ① 轮询检测（feishu_contract_loop.py）
                        ▼
        ┌──────────────────────────────────────────────┐
        │  ② 读取合同内容                                │
        │  lark-cli docs +fetch --doc-format markdown   │
        └───────────────┬──────────────────────────────┘
                        │ ③ 本地审核引擎
                        ▼
        ┌──────────────────────────────────────────────┐
        │  规则引擎 26 项检查（零 token）                 │
        │  + 可选 LLM 终局决策（SenseChat-5）            │
        │  + Token 消耗计量 & 节省量化                   │
        └───────────────┬──────────────────────────────┘
                        │ ④ 沉淀回飞书
                        ▼
        ┌──────────────────────────────────────────────┐
        │  ⑤ 审核报告文档                                │
        │  wiki +node-create + docs +update             │
        ├──────────────────────────────────────────────┤
        │  ⑥ 多维表格结构化记录                           │
        │  lark-cli base +record-upsert                 │
        │  字段：合同、结论、通过率、风险数、Token、链接   │
        ├──────────────────────────────────────────────┤
        │  ⑦ 主体画像文档（每个乙方一份档案）              │
        │  审核历史自动累积 + 尽调节占位                  │
        └───────────────┬──────────────────────────────┘
                        │ ⑧ 小浣熊联网尽调（Skill / MCP 编排）
                        ▼
        ┌──────────────────────────────────────────────┐
        │  小浣熊定时任务读取 pending_due_diligence      │
        │  → 联网检索工商/失信/涉诉/负面（附来源链接）    │
        │  → --write-dd（Skill CLI）或                  │
        │    write_due_diligence（MCP 工具）回填画像     │
        └──────────────────────────────────────────────┘
```

---

## 二、触发方式：定时轮询

采用**定时轮询**模式（非实时 Webhook），理由：
- 无需公网端点，本地即可运行
- 配合 cron 或小浣熊定时任务，每工作日自动执行
- 实现简单，稳定可靠

### 轮询逻辑

1. `lark-cli wiki +node-list` 列出知识库指定节点下的子文档
2. 对比本地状态文件 `scripts/.feishu_loop_state.json`，过滤已处理文档
3. 对新增的 docx 类型文档触发审核
4. 审核完成后更新状态文件，下次轮询跳过

### 与小浣熊定时任务的衔接

**推荐（MCP）**：小浣熊桌面端 2.0 → MCP 连接器 → `feishu_loop_mcp_server.py` → 定时任务调用 `run_feishu_loop`。配置见 [`docs/XIAOHUANXIONG_MCP_SETUP.md`](XIAOHUANXIONG_MCP_SETUP.md)。

**Fallback**：
- Skill 脚本：`uv run python scripts/feishu_contract_loop.py`（见 `.cursor/skills/feishu-contract-loop/SKILL.md`）
- HTTP Webhook：`POST http://127.0.0.1:8765/api/feishu-loop`（需先 `uv run crew_gui`）

可与每日 09:00 的小浣熊定时任务配合：小浣熊触发闭环 → 脚本轮询飞书知识库 → 三层 skill 审核 → 写回 → 小浣熊后续步骤可读取多维表格做周报数据分析。

---

## 三、沉淀方式：报告文档 + 多维表格

### 审核报告文档

两步写回（`docs +create --wiki-space` 在当前 lark-cli 版本不会挂到 wiki 节点，故分两步）：
1. `lark-cli wiki +node-create --space-id <id> --obj-type docx --title "【审核报告】{合同名} · {日期}"` 在知识库建一个 docx 节点（确保挂到 wiki，拿到 `obj_token` + `url`）
2. `lark-cli docs +update --api-version v2 --doc <obj_token> --command overwrite --doc-format markdown --content -`（经 stdin 传 Markdown，规避 `@file` 必须相对路径的限制）

> 注：`docs +update --command overwrite` 会用报告 Markdown 的 H1 覆盖文档标题，故节点最终标题取自报告 H1（如「合同审核报告」）。`detect_new_contracts()` 据此过滤标题含「审核报告」的节点，避免闭环把自己的报告当成新合同反复审核。

- 内容含：总体结论、维度对照表、修改建议、Token 消耗对比

### 多维表格结构化记录

写入多维表格（`lark-cli base +record-upsert`），字段设计：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| 合同文件 | 文本 | 合同文档标题 |
| 总体结论 | 文本 | 审核不通过 / 需修订 / 通过 |
| 通过率 | 数字 | 规则通过率 % |
| 高风险数 | 数字 | 高风险不通过项数 |
| 中风险数 | 数字 | 中风险不通过项数 |
| 低风险数 | 数字 | 低风险不通过项数 |
| Token消耗 | 数字 | 混合架构实际 token |
| Token节省 | 数字 | 相对纯 LLM 节省 % |
| 审核时间 | 日期 | 审核时间戳 |
| 原文链接 | 链接 | 飞书合同文档 URL |
| 审核报告 | 文本 | 报告摘要（≤2000字） |

多维表格的作用：
- 结构化沉淀，支持筛选、排序、视图配置
- 周报数据分析的数据源（小浣熊数据分析能力可读取）
- 主体画像和风险案例的索引

---

## 四、主体画像写回：卡点分析与重构

> 复赛评审可能追问「主体画像写回为什么初版没实现、卡点是什么」。如实说明如下。

### 初版为什么没实现

初版把「主体画像 + 案例摘要写回知识库」写在**云端小浣熊的七步 Agent Prompt** 里（第 6 步），期望云端 Agent 自己完成。实际卡点有两个：

| 卡点 | 具体表现 |
| --- | --- |
| **写入通道够不到** | 云端小浣熊工作台没有本项目的飞书 lark-cli 凭证，它「说」写入知识库，实际只能写进小浣熊自己的会话知识库，**到不了企业飞书 wiki**。这是通道问题，不是能力问题。 |
| **联网尽调依赖环境** | 画像的核心价值是尽调信息，而部分小浣熊会话无联网工具（实测返回「没有可用的联网检索工具」），画像内容无从获得。本地管线也没有搜索 API key（SenseNova search 需 key）。 |

### 重构方案：按「谁有什么能力」重新分工

结论是**这不是不能实现，而是初版分工放错了位置**。重构后：

```
主体画像 = 审核历史（本地闭环写） + 联网尽调（小浣熊查、经 MCP 写回）
```

- **审核历史**：规则引擎本来就抽取乙方名称（`fields.party_b`），闭环每审一份合同就把
  {日期、结论、通过率、高风险数、报告链接} 并入该乙方的画像文档（`【主体画像】<乙方名>`），
  用 `wiki +node-create` + `docs +update --command overwrite` 写回——与审核报告同一条已验证的通道。
- **联网尽调**：小浣熊桌面端**原生有联网检索**。闭环返回
  `pending_due_diligence`（待尽调主体清单），小浣熊定时任务对每个主体联网检索后，
  经 `contract-review-loop` Skill 的 `--write-dd` 命令（或 MCP 工具 `write_due_diligence`）
  把尽调结论（附来源链接）合并进画像文档。

各用所长：本地 skill 做「精确 + 有凭证」的事，小浣熊做「联网 + 编排」的事，**全流程无降级**。

### 实证（2026-07-03）

| 主体 | 画像文档 | 内容 |
| --- | --- | --- |
| 北京智链数科技术有限公司 | https://my.feishu.cn/wiki/DsZSwpZc1iRALIknUN2cvesxn7U | 审核历史（128万合同）+ 尽调结论（查无精确匹配主体——脱敏样本的诚实结论，附复查渠道） |
| 深圳智能设备有限公司 | https://my.feishu.cn/wiki/IFJcwWVDBiUCQwkaUxOcLn5Rnpf | 审核历史（200万合同）+ 尽调结论（同上） |

> 注：两份样本合同均为脱敏样本，乙方名称非真实主体，联网检索如实返回「查无精确匹配」——
> 这本身就是尽调链路正确工作的证明（查不到的主体应作为高风险信号提示人工核实，而不是编造工商信息）。

---

---

## 五、配置与运行

### 1. 配置飞书知识库

在 `.env` 中配置（参见 `.env.example`）：

```bash
# 获取 space_id
lark-cli wiki +space-list --as user --format json

# 获取节点 token（列出知识库节点）
lark-cli wiki +node-list --space-id <SPACE_ID> --as user --format json

# 配置
FEISHU_WIKI_SPACE_ID=SpaceIDxxxxx
FEISHU_CONTRACT_NODE=NodeTokenForContracts
FEISHU_REPORT_NODE=NodeTokenForReports
FEISHU_BITABLE_APP=BaseAppTokenxxxxx
FEISHU_BITABLE_TABLE=合同审核记录
FEISHU_LOOP_REVIEW_MODE=rules_only
```

### 2. 首次确认节点

```bash
uv run python scripts/feishu_contract_loop.py --list-nodes
```

列出知识库所有节点，确认合同目录和报告目录的 node_token。

### 3. 运行轮询

```bash
# 单次轮询（检测新合同 → 审核 → 写回）
uv run python scripts/feishu_contract_loop.py

# 干跑（只列出节点，不执行审核和写回）
uv run python scripts/feishu_contract_loop.py --dry-run
```

### 4. 配合 cron 定时

```bash
# 每工作日 09:30 轮询飞书知识库
30 9 * * 1-5 cd /path/to/local_crewai_demo && uv run python scripts/feishu_contract_loop.py >> logs/feishu_loop.log 2>&1
```

---

## 六、代码索引

| 模块 | 文件 | 关键函数 |
| --- | --- | --- |
| 轮询编排 | `scripts/feishu_contract_loop.py` | `run_once()`, `list_wiki_nodes()`, `detect_new_contracts()` |
| 读取合同 | `scripts/feishu_contract_loop.py` | `fetch_doc_content()` → `lark-cli docs +fetch` |
| 本地审核 | `src/local_crewai_demo/gui.py` | `_run_contract_review()`（复用 GUI 审核引擎） |
| 报告写回 | `scripts/feishu_contract_loop.py` | `create_report_doc()` → `wiki +node-create` + `docs +update --command overwrite` |
| 多维表格 | `scripts/feishu_contract_loop.py` | `write_bitable_record()` → `lark-cli base +record-upsert` |
| 状态持久化 | `scripts/.feishu_loop_state.json` | `processed`（已处理文档）+ `profiles`（主体画像与尽调状态） |
| 主体画像 | `scripts/feishu_contract_loop.py` | `extract_counterparty()`, `record_contract_to_profile()`, `upsert_profile_doc()`, `write_due_diligence()`, `get_pending_due_diligence()` |
| MCP 接入 | `scripts/feishu_loop_mcp_server.py` | `run_feishu_loop`, `get_pending_due_diligence`, `write_due_diligence`, `audit_contract_text`, `list_feishu_wiki_nodes` |
| HTTP 触发 | `src/local_crewai_demo/gui.py` | `POST /api/feishu-loop` |
| 小浣熊配置 | `docs/XIAOHUANXIONG_MCP_SETUP.md` | MCP 连接器 + 定时任务 Prompt |

---

## 七、扩展方向

| 方向 | 说明 |
| --- | --- |
| 实时 Webhook | 如需实时触发，可改用飞书事件订阅 + 公网端点（ngrok/cloudflare tunnel），把 `/api/webhook/feishu` 端点加到 GUI HTTP 服务 |
| 附件合同审核 | 当前读取飞书文档内容；如合同以附件形式存在，可扩展 `lark-cli drive +download` 下载附件后走 PDF→Markdown 流程 |
| 主体画像沉淀 | 多维表格可扩展「对方主体画像」表，联网尽调结果写入，跨合同复用 |
| 周报自动生成 | 多维表格作为数据源，小浣熊周五定时任务读取并生成周报 PPT |

---

## 八、实证记录（2026-07-03 端到端跑通）

> 本节为复赛前真实端到端运行留证，路演时可现场打开下列飞书链接展示。

### 资源清单

| 资源 | 名称 | 标识 / URL |
| --- | --- | --- |
| 知识库空间 | 合同审查闭环demo | `7657968260024913086` |
| 待审合同（docx） | 脱敏样本合同-软件服务128万 | https://my.feishu.cn/wiki/JBPjwrVFniIBSYkcuZAcegManjg |
| 审核报告（docx，闭环自动写回） | 合同审核报告 | https://my.feishu.cn/wiki/M89yw9Uj5iKdxukSUjBcGe8gnSe |
| 多维表格 | 合同审查记录 / 审核记录表 | https://my.feishu.cn/base/TKEdbShCyaWqa4sAnoVc9FG5nbg |
| 结构化记录 | NO.001（首条闭环沉淀） | `record_id=recvoeB1MmNoBO`，表 `tblqAZavMQaIZUR9` |
| 主体画像（docx，闭环自动写回） | 【主体画像】北京智链数科技术有限公司 | https://my.feishu.cn/wiki/DsZSwpZc1iRALIknUN2cvesxn7U |
| 主体画像（docx，闭环自动写回） | 【主体画像】深圳智能设备有限公司 | https://my.feishu.cn/wiki/IFJcwWVDBiUCQwkaUxOcLn5Rnpf |

### 审核结果（rules_only · 零 LLM token）

- 合同金额：**1,280,000.00 元**（128 万软件服务合同）
- 总体结论：**审核不通过（存在 3 项高风险）**
- 规则统计：通过 17 / 26，不通过 6，需复核 3 → 通过率 **65.4%**
- 风险分布：高风险 **3**、中风险 2、低风险 1
- **3 项高风险命中**：
  - R09 税率合理性 → 识别不合规税率 **30%**（应为 6/9/13/1/3%/免税/0% 之一）
  - R10 付款比例合计 → 各阶段合计仅 **0.03%**（应等于 100%）
  - R23 争议解决方式唯一性 → 同时约定仲裁与诉讼，方式冲突
- Token 计量：混合架构实耗 **14,931 token**，相对纯 LLM 节省 **17.6%**
- 效率：单份人工约 4h → 混合架构约 3min（**估算**，非计时实测）

### 审核结果（rules_agent · LLM 复核 · NO.002 · 2026-07-03）

- 合同：**脱敏样本合同-智能硬件200万**（793 字符）
- 模式：`rules_agent` + DeepSeek（SenseChat key 未配置时的演示 LLM）
- 总体结论：**不通过（需退回修改）**
- 规则统计：通过率 **69.2%**，高风险 **2**、中风险 1、低风险 2
- Token：混合架构 **13,729 token**，节省 **14.7%**
- 报告写回：https://my.feishu.cn/wiki/GGZ1w8UAAitfnqksJXIc2GxVnL1
- 原文：https://my.feishu.cn/wiki/M8tewyKTviWOklkNxsucjm2Wn2d

### 多维表格写入字段（NO.001 实测值）

`合同文件=脱敏样本合同-软件服务128万`、`通过率=65.4`、`高风险数=3`、`中风险数=2`、`低风险数=1`、`Token消耗=14931`、`Token节省=17.6`、`审核时间=2026-07-03 00:36`、`原文链接=合同 wiki URL`、`审核报告=2713 字全文`。

### 复现命令

```bash
# 1. 已在 .env 配好 FEISHU_WIKI_SPACE_ID / FEISHU_BITABLE_APP / FEISHU_BITABLE_TABLE
# 2. 清空已处理状态后单次轮询（检测合同 → 审核 → 写回报告 + 多维表格）
rm -f scripts/.feishu_loop_state.json
uv run python scripts/feishu_contract_loop.py
# 3. 仅列出知识库节点（首次配置确认）
uv run python scripts/feishu_contract_loop.py --list-nodes
```

### lark-cli 权限要求

闭环需 user 身份授予：`wiki:space:write_only`、`wiki:node:create`、`wiki:node:read`、`docx:document:create`、`docx:document:write_only`、`docs:document.content:read`、`base:app:create`、`base:table:create`、`base:field:create`、`base:record:create`。缺权限时用 `lark-cli auth login --domain wiki,base,docs,drive --no-wait --json` 重新授权补齐。
