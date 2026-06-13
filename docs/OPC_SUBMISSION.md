# OPC 高手创造赛 · 作品提交材料

> 作品名称：**办公小浣熊 · 企业合同初审工作台**  
> 赛事页面：[小浣熊挑战季 · OPC 高手创造赛](https://community.xiaohuanxiong.com/2026-spring/detail)  
> 学习手册：[Datawhale 赛事入门](https://ailc.datawhale.cn/hall/group/236/task/334/)

---

## 一、作品简介（约 300 字）

**痛点**：企业采购/法务部门初审合同时，需法务审条款、财务核金额税率、业务确认付款节点，单份合同平均耗时 4 小时，且金额大小写、付款比例、争议解决冲突等项易漏检。

**方案**：基于 **办公小浣熊 / SenseNova（SenseChat-5）** 构建「合同初审 OPC 工作台」，串联 **文档处理 → 知识库 → 数据分析 → 文案报告 → 汇报大纲** 五大模块。本地 22 条规则引擎负责确定性计算校验，小浣熊 Agent 结合 `knowledge/contract_audit_kb.md` 知识库完成语义复核与报告润色，并自动生成 6 页管理层汇报大纲（可导入小浣熊 PPT 生成）。

**成效**：单份合同审核从约 **4 小时降至 3 分钟**，22 项规则全覆盖；实测 `realistic_software_service_contract.txt` 检出 3 项高风险、6 项不通过，合规通过率 59%。可体验 Demo：`uv run crew_gui`。

---

## 二、场景与痛点 (Why)

| 维度 | 传统方案 | 本作品 |
| --- | --- | --- |
| 人力 | 法务 + 财务双线，≥2 人 | **1 人 + 办公小浣熊** |
| 耗时 | 单份约 4 小时 | 约 3 分钟 |
| 计算项 | Excel 手算，易错 | 22 条规则引擎秒级校验 |
| 语义项 | 依赖个人经验 | 知识库红线 + SenseChat 复核 |
| 交付物 | 零散批注 | 审核报告 + 数据洞察 + PPT 大纲 |

---

## 三、解决方案与实操 (How) — 核心评审项

### 3.1 小浣熊能力模块组合

```
上传合同
   ↓ 文档处理（PDF/DOCX/TXT 解析 + 字段抽取）
   ↓ 知识库（contract_audit_kb.md 法务红线）
   ↓ 数据分析（合规率、风险分布、分组通过率）
   ↓ 文案（SenseChat-5 生成 Markdown 审核报告）
   ↓ 汇报/PPT（6 页管理层汇报大纲 → 可导入小浣熊 PPT）
```

### 3.2 核心 Prompt

完整 Prompt 见 [`prompts/xiaohuanxiong_core_prompts.md`](../prompts/xiaohuanxiong_core_prompts.md)。

**审核报告 Prompt（节选）**：

```
你将审核合同《{file_name}》。知识库要点：{knowledge_context}
结构化证据：{audit_evidence_json}
请生成 Markdown 审核报告，不得改变通过/不通过/需复核判断。
```

**汇报大纲 Prompt（节选）**：

```
基于审核结论生成 6 页汇报 PPT 大纲：封面、背景、关键数据、合规总览、Top 风险、决策建议。
每页 ≤5 要点，可直接粘贴至办公小浣熊 PPT 生成。
```

### 3.3 关键操作截图建议（提交 PPT 时附 3–5 张）

1. 办公小浣熊网页端 + 知识库上传 `contract_audit_kb.md` 的对话截图  
2. 本 Demo 上传 `realistic_software_service_contract.txt` 的审核界面  
3. 「数据洞察」Tab 的合规率与风险分布  
4. SenseChat 生成的审核报告（Markdown 渲染）  
5. 「汇报大纲」Tab + 粘贴至小浣熊 PPT 生成的过程  

### 3.4 方案独特性

- **规则引擎 + 大模型分工**：计算类 22 条规则确定性校验，LLM 只做语义润色与汇报，避免「算错金额」幻觉  
- **知识库可复用**：法务红线沉淀为 `knowledge/`，可 @ 引用扩展  
- **全链路可演示**：无 API Key 时仍可跑规则+数据分析+汇报模板；有 Key 时跑完整小浣熊 Agent 链路  

---

## 四、成果与价值 (What)

### 交付物

| 产物 | 路径/入口 |
| --- | --- |
| 可体验 Demo | `uv run crew_gui` → http://127.0.0.1:7860 |
| 审核报告 | 界面「报告」Tab（Markdown） |
| 结构化 JSON | 界面「JSON」Tab |
| 数据洞察 | 界面「数据洞察」Tab |
| 汇报大纲 | 界面「汇报大纲」Tab |
| 真实合同样本 | `knowledge/realistic_software_service_contract.txt` |

### 量化数据

- 规则覆盖：**22 条 / 3 组**（财务 12 + 法务 7 + 文本 3）  
- 效率提升：4h → 3min（**约 92%** 时间节省，界面展示）  
- 实测样本：`realistic_software_service_contract.txt` → 13/22 通过，3 项高风险  

---

## 五、环境配置

```bash
# .env
SENSENOVA_API_KEY=你的商汤API密钥
MODEL=openai/SenseChat-5
BASE_URL=https://api.sensenova.cn/compatible-mode/v2
```

报名高手创造赛并提交作品想法后，可申请 **15 天会员卡或 API Token** 支持。

---

## 六、评审维度对照

| 评审维度 | 权重 | 本作品对应 |
| --- | --- | --- |
| 场景真实性与闭环验证 | 35% | 企业合同初审真实场景，Demo 可跑通，有量化效率数据 |
| 商业价值与可持续性 | 30% | 法务/采购部门可复用，知识库与规则可扩展 |
| 工具整合与替代能力 | 25% | 文档+知识库+数据分析+文案+PPT 五模块协同 |
| 表达清晰度 | 10% | 本文档 + 可体验 Demo + Markdown 报告 |
