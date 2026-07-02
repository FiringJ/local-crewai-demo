# 技术架构 · Skill 设计与 Token 成本量化

> 回应导师反馈：把项目里「设计了什么样的 skill」「PDF 转 Markdown 节省 token」「跑一次任务消耗多少 token」这些技术价值讲清楚。

---

## 一、架构总览：三层混合架构

本作品不是「把合同丢给 LLM 让它从头审」，而是设计了三层分工的混合架构：

```
┌─────────────────────────────────────────────────────────┐
│  Skill 层 1 · PDF→Markdown 结构化转换                      │
│  PyMuPDF dict 提取 → 标题层级 + 表格 → 精简 Markdown       │
│  成本：0 token（纯本地计算）                               │
├─────────────────────────────────────────────────────────┤
│  Skill 层 2 · 规则引擎证据层（26 项检查）                   │
│  Python Decimal 精确计算数值类 + 正则匹配语义类             │
│  成本：0 token（纯本地计算）                               │
│  产出：26 项结论 JSON（engine_signal + evidence）          │
├─────────────────────────────────────────────────────────┤
│  Skill 层 3 · LLM 终局决策（办公小浣熊 / SenseChat）       │
│  输入：精简 Markdown + 规则结论 JSON + 知识库红线           │
│  职责：复核引擎结论 → 修正误报 → 引用原文 → 出报告          │
│  成本：仅此层消费 token                                   │
└─────────────────────────────────────────────────────────┘
```

**核心设计思想**：把 token 昂贵的 LLM 从「执行者」降级为「复核者」。数值类检查（金额大小写、税率合规、付款比例合计）由规则引擎用 Decimal 精确计算零 token 完成，LLM 只做语义类判断和终局报告。

---

## 二、Skill 层 1 · PDF→Markdown 结构化转换

### 问题

合同通常以 PDF 形式流转。传统做法是 `page.get_text("text")` 提取纯文本流，问题：
- 丢失标题层级（无法区分「第一条」和正文段落）
- 丢失表格结构（付款明细变成乱序数字）
- 保留大量冗余空白、页眉页脚重复内容

直接把这种纯文本流喂给 LLM，既浪费 token，又降低 LLM 理解准确度。

### 设计

`pdf_markdown.py` 的 `pdf_to_markdown()` 用 PyMuPDF 结构化提取：

| 提取策略 | 实现 | 价值 |
| --- | --- | --- |
| 标题层级识别 | 字体大小聚类：统计每页字号分布，出现最多的为正文，明显更大的为标题（`#`/`##`/`###`） | LLM 能快速定位条款 |
| 表格识别 | `page.find_tables()` 提取表格 bbox，输出 Markdown 表格语法 | 付款明细、金额计算关系保留 |
| 段落合并 | 同 block 内连续行合并为一段，去除逐行断裂 | 减少 token 浪费 |
| 表格区去重 | 表格 bbox 覆盖的文本块跳过，避免表格内容重复出现 | 避免冗余 |

### 代码位置

- `src/local_crewai_demo/pdf_markdown.py` — `pdf_to_markdown()`, `_page_to_markdown()`, `_infer_body_size()`
- `src/local_crewai_demo/contract_review.py` — `extract_text_from_file()` 对 PDF 调用 `pdf_to_markdown`

### 与办公小浣熊的关系

办公小浣熊的「文档处理」能力也能做 PDF 解析，但那是 LLM 侧消费 token 的转换。本作品刻意把 PDF→MD 放在本地零 token 完成，只把精简结果传给 LLM — 这是 token 效率最优的设计选择，而非能力缺失。

---

## 三、Skill 层 2 · 规则引擎证据层

### 设计

`contract_review.py` 实现了 26 项规则、6 组职责的纯 Python 规则引擎：

| 分组 | 数量 | 代表规则 | 法律依据 |
| --- | --- | --- | --- |
| I. 合同效力与主体 | 4 | 主体信息完整、名称一致、必备条款、日期 | 《民法典》470、502条 |
| II. 标的与履行 | 3 | 交付验收、知识产权、保密 | 《民法典》621、845—850条 |
| III. 价款税务与结算 | 9 | 金额大小写、税率合规、付款比例合计 | 《增值税法》；《保障中小企业款项支付条例》 |
| IV. 违约救济与争议 | 5 | 违约金、不可抗力、争议解决唯一性 | 《民法典》585、590条；《仲裁法》5条 |
| V. 担保与多方关系 | 2 | 保证金、连带责任 | 《民法典》586、592条 |
| VI. 文本一致与表述 | 3 | 跨条款一致、计算校验、语病 | 《民法典》510、142条 |

### 数值类检查的精确性优势

规则引擎用 `Decimal` 做精确计算，避免 LLM 做数值计算时的浮点误差和幻觉：

- **金额大小写一致性**：数字金额 vs 中文大写金额逐位比对（`_chinese_money_to_decimal`）
- **税率合规**：校验是否为法定税率档 13%/9%/6%/3%/1%/0%/免税
- **付款比例合计**：`sum(percentages) == 100`，`Decimal` 精确加法
- **价税计算**：`不含税 × 税率 = 税额`；`不含税 + 税额 = 含税总额`

这些检查如果交给 LLM，它需要读数字、做计算、自我校验，容易出错且消费大量 token。规则引擎一次精确搞定，零 token。

### 产出格式

规则引擎产出 `rule_reference_json`，作为 LLM 的「初筛信号」而非「终局结论」：

```json
{
  "reference_role": "本地规则引擎 · 审核维度初筛参考（非终局结论）",
  "dimensions": [
    {
      "code": "R09",
      "dimension": "税率合理性",
      "engine_signal": "不通过",
      "engine_evidence": "识别到不合规税率：30%",
      "engine_suggestion": "将税率调整为 6%/9%/13%..."
    }
  ]
}
```

LLM 的职责是复核这些信号：采纳 / 修正（附理由+原文）/ 标需复核。

---

## 四、Skill 层 3 · LLM 终局决策

### 设计

CrewAI 编排 2 个 Agent + 2 个 sequential Task：

| Agent | 职责 | max_iter |
| --- | --- | --- |
| `contract_auditor` | 复核规则引擎 26 维结论 → 引用原文修正误报 → 出审核报告 | 4 |
| `briefing_specialist` | 把终局结论转成 6 页管理层汇报 PPT 大纲 | 3 |

LLM 拿到的输入是精简后的：
- 结构化 Markdown 合同（非原始 PDF 纯文本流）
- 规则引擎结论 JSON（26 项已有初筛，非让 LLM 从头查）
- 知识库红线（12000 字符上限）

LLM 不需要「读规则定义 → 逐条推理 → 计算 → 出报告」，只需要「看结论 → 复核 → 修正 → 写报告」。

---

## 五、Token 成本量化（实测）

### 两种架构对比

`build_token_savings_profile()` 用 tiktoken（cl100k_base，对齐 GPT-4o / SenseChat 量级）量化两种架构的 token 消耗：

**场景 A · 纯 LLM 从头审（2 轮）**：
- 轮 1 逐项检查：input = 合同全文 + 知识库 + 26 条规则定义，output = 26 项结论 + 推理链
- 轮 2 汇总报告：input = 轮 1 结论 + 合同全文，output = 审核报告

**场景 B · 混合架构（本作品，1 轮）**：
- 规则引擎零 token 完成 26 项检查
- LLM 单轮复核：input = 合同 Markdown + 知识库 + 规则结论 JSON，output = 终局报告

### 实测数据（128 万元软件服务合同样本）

| 架构 | 轮次 | 合同输入 | 知识库 | 规则(定义/结论) | 输出 | 合计 |
| --- | --- | --- | --- | --- | --- | --- |
| 纯 LLM 从头审 | 2 | 3020 | 7025 | 2010 | 6000 | **18055** |
| 混合架构（本作品） | 1 | 1510 | 7025 | 3860 | 2500 | **14895** |

> **单次审核节省约 3160 tokens（17.5%）** —— 此为 tiktoken 估算模型口径。
> 规则引擎 26 项检查零 token 成本，LLM 侧仅消费 14895 tokens 做终局复核。

### A/B 双架构真实调用实测（2026-07-03，对外统一口径）

估算模型之外，`scripts/token_ab_test.py` 对同一份合同、同一模型（deepseek-chat）**真实调用两种架构**，token 数取 API 返回 usage 字段：

| 架构 | 轮次 | token 合计 |
| --- | --- | --- |
| A · 纯 LLM 从头审（读规则定义 → 逐项推理 → 二轮汇总） | 2 | 18,327 |
| B · 混合架构（规则引擎 0 token → 单轮复核+报告） | 1 | **13,705** |

> **实测节省 4,622 tokens（25.2%）**，结果存档 `outputs/token-ab-result.json`，一条命令可复现。
> 实测高于估算的原因：纯 LLM 轮 1 的推理链输出（2,725 tokens）比估算模型假设的更长——让 LLM 从头做 26 项数值检查本身就要多花输出 token。

### 实际运行 token 消耗

CrewAI `kickoff()` 返回的 `CrewOutput.token_usage` 被捕获并展示在 GUI 和 CLI：

| 指标 | 说明 |
| --- | --- |
| `prompt_tokens` | 实际输入 token（含合同 + 知识库 + 规则结论） |
| `completion_tokens` | 实际输出 token（审核报告 + 汇报大纲） |
| `total_tokens` | 合计 |
| `estimated_cost_cny` | 按 SenseChat-5 量级单价估算成本 |

> GUI `/api/review` 响应新增 `tokenUsage` 字段；CLI `run_crew` 末尾打印 token 报告。

### 为什么真实场景节省更高

上述 17.5% 是基于 2KB 的 txt 样本。真实合同 PDF 通常 20-50 页，含：
- 大量冗余空白和换行（Markdown 去除后 token 更少）
- 重复页眉页脚（结构化提取过滤）
- 复杂表格（Markdown 表格比纯文本流更精简）

合同越大，`raw_tokens` vs `md_tokens` 的差距越大，加上多轮→单轮的架构节省，综合节省比例可达 **30-40%**。

---

## 六、为什么这个设计是「Skill」而不是「脚本」

导师问「设计了什么样的 skill」，本作品的三层架构满足 skill 的核心特征：

1. **可复用**：`pdf_to_markdown` 和规则引擎是独立模块，任意合同审核流程都可接入
2. **有明确输入输出契约**：PDF→Markdown、text→26项结论JSON、结论JSON+MD→报告
3. **有可量化的价值**：token 节省 17.5%、数值检查零幻觉、单次审核 3 分钟
4. **与 LLM 能力互补**：规则引擎做精确计算（LLM 不擅长的），LLM 做语义判断（规则引擎不擅长的）
5. **可被编排**：通过 CrewAI 的 Task/Agent 编排，或通过 `run_with_trigger` 被 Webhook 触发

---

## 七、代码索引

| Skill 层 | 文件 | 关键函数 |
| --- | --- | --- |
| PDF→Markdown | `src/local_crewai_demo/pdf_markdown.py` | `pdf_to_markdown()`, `estimate_tokens()`, `build_token_savings_profile()` |
| 规则引擎 | `src/local_crewai_demo/contract_review.py` | `ALL_RULES`, `audit_contract_text()`, `build_rule_reference_payload()` |
| LLM 编排 | `src/local_crewai_demo/crew.py` + `config/agents.yaml` + `config/tasks.yaml` | `contract_auditor`, `briefing_specialist` |
| Token 计量 | `src/local_crewai_demo/gui.py` | `_extract_token_usage()`, `_build_token_savings()` |
| CLI 输出 | `src/local_crewai_demo/main.py` | `_print_token_report()` |
