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

# 办公小浣熊 · 企业合同初审工作台

> **商汤小浣熊 OPC 高手创造赛**参赛作品 — 一人 + AI 跑通企业合同初审全链路。

真实场景：采购/法务部门合同初审。串联办公小浣熊五大能力模块：

| 模块 | 能力 | 本作品落地 |
| --- | --- | --- |
| 文档处理 | 合同解析 | PDF/DOCX/TXT 抽取 + 字段识别 |
| 知识库 | @知识库 复核 | `knowledge/contract_audit_kb.md` |
| 数据分析 | 合规洞察 | 通过率、风险分布、分组统计 |
| 文案 | 审核报告 | SenseChat-5 生成 Markdown 报告 |
| 汇报/PPT | 管理层简报 | 6 页汇报大纲 → 可导入小浣熊 PPT |

参赛材料见 [`docs/OPC_SUBMISSION.md`](docs/OPC_SUBMISSION.md)，核心 Prompt 见 [`prompts/xiaohuanxiong_core_prompts.md`](prompts/xiaohuanxiong_core_prompts.md)。

---

基于 CrewAI + SenseNova API 实现，核心流程：

- 合同文件上传或正文粘贴
- PDF / DOCX / TXT 文本抽取
- 3 组 22 条规则审核
- 金额、税率、付款比例等确定性计算校验
- JSON 结构化结果与 Markdown 审核报告
- 可选 CrewAI Agent 对结构化结果进行报告润色

## 运行

### 前端（React + shadcn/ui）

```bash
cd frontend
npm install
npm run build
```

开发模式（Vite 会将 `/api` 代理到后端）：

```bash
# 终端 1：后端 API
uv run crew_gui --no-open --port 7860

# 终端 2：前端开发服务器
cd frontend && npm run dev
```

### 启动 GUI

```bash
uv run crew_gui --no-open
```

若已执行 `npm run build`，`crew_gui` 会自动托管 `frontend/dist` 中的 React 界面；否则回退到 `src/local_crewai_demo/web` 旧版静态页。

打开终端输出的本地地址，上传合同文件后点击“开始审核”。

命令行运行示例：

```bash
uv run run_crew knowledge/sample_contract.txt
```

## 审核模式

- `小浣熊全链路（推荐）`：规则引擎 → 知识库 → 数据分析 → SenseChat 报告 + 汇报大纲（需 `SENSENOVA_API_KEY`）。
- `仅规则引擎（离线演示）`：不调用 LLM，仍可输出规则报告、数据洞察、汇报模板。

## LLM 配置（办公小浣熊 / SenseNova）

默认使用商汤 SenseNova OpenAI 兼容接口（办公小浣熊同款模型能力），请在 `.env` 中配置：

```bash
SENSENOVA_API_KEY=你的商汤API密钥
MODEL=openai/SenseChat-5
BASE_URL=https://api.sensenova.cn/compatible-mode/v2
```

可参考 `.env.example`。密钥可在 [商汤大装置](https://www.sensecore.cn) 控制台获取。

## 测试合同样本

- `knowledge/sample_contract.txt` — 演示用采购合同（含税率/付款比例等问题）
- `knowledge/realistic_software_service_contract.txt` — 更贴近真实的软件实施服务合同（含争议解决冲突等条款）

## 规则覆盖

规则来自技术方案，覆盖财务条款、法务合规、文本质量三类：

- 财务条款审核：12 条
- 法务合规审核：7 条
- 文本质量审核：3 条

规则定义和实现位于 `src/local_crewai_demo/contract_review.py`。

## 云端部署见 [`docs/DEPLOY_NO_CARD.md`](docs/DEPLOY_NO_CARD.md)（**免绑卡**：Hugging Face Spaces / Cloudflare 隧道）。

```bash
# 本地验证 Docker 镜像
docker build -t contract-audit .
docker run --rm -p 7860:7860 -e PORT=7860 -e DEEPSEEK_API_KEY=你的key contract-audit
```
