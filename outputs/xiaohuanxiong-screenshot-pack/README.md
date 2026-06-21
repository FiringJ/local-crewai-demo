# 小浣熊真实过程截图整理包

目标：补齐评委最关心的“真实使用小浣熊能力”的过程证据。截图可以来自网页端，也可以来自桌面端；关键不是端形态，而是画面里能看到能力、输入、过程和输出。

## 截图命名与目录

| 编号 | 文件名建议 | 目录 | 需要证明的能力 |
|---|---|---|---|
| S01 | `01-timed-task/create-daily-contract-review.png` | `01-timed-task/` | 工作日 09:00 定时任务 |
| S02 | `01-timed-task/create-weekly-briefing.png` | `01-timed-task/` | 周五 17:00 周报定时任务 |
| S03 | `02-agent-orchestration/multi-step-agent-plan.png` | `02-agent-orchestration/` | Agent 编排每日流水线 |
| S04 | `03-document-parse/upload-contract-and-extract.png` | `03-document-parse/` | 上传合同、解析正文、抽字段 |
| S05 | `04-web-search-due-diligence/search-party-profile.png` | `04-web-search-due-diligence/` | 联网检索乙方工商/涉诉/经营异常/负面 |
| S06 | `05-knowledge-write/save-party-profile.png` | `05-knowledge-write/` | 写入「对方主体画像库」 |
| S07 | `06-knowledge-read/at-kb-redline-review.png` | `06-knowledge-read/` | @知识库 调取历史画像和法务红线 |
| S08 | `07-data-analysis/weekly-risk-analysis-chart.png` | `07-data-analysis/` | 数据分析提问与图表 |
| S09 | `08-ppt-generation/generate-weekly-ppt.png` | `08-ppt-generation/` | 自动生成合同初审周报 PPT |
| S10 | `09-iteration-dialogue/multi-turn-tuning.png` | `09-iteration-dialogue/` | 多轮调优对话，体现过程 |
| S11 | `10-final-review/final-artifacts-overview.png` | `10-final-review/` | 报告、PPT、知识库、数据分析产物总览 |

## 建议拍摄顺序

### S01 每日定时任务

画面需要同时出现：

- 任务名称：`工作日 09:00 合同初审每日流水线`
- 调度时间：工作日 09:00
- 任务描述：自动拉取昨日新增待审合同，逐份完成解析、主体尽调、规则证据、报告生成和高风险推送

可粘贴 Prompt：

```text
请创建一个工作日 09:00 自动执行的合同初审每日流水线：
1. 拉取昨日新增待审合同：OA待签、邮箱附件、共享盘；
2. 对每份合同解析正文并抽取主体、金额、税率、付款、期限字段；
3. 联网检索乙方工商、涉诉失信、经营异常与负面信息；
4. 把主体尽调结果写入「对方主体画像库」；
5. @知识库 调取历史画像和法务红线；
6. 使用 22 条确定性规则证据生成 Markdown 初审报告；
7. 高风险合同即时推送法务，结论归档到「合同风险案例库」。
```

### S02 每周周报定时任务

画面需要同时出现：

- 任务名称：`周五 17:00 合同初审周报`
- 调度时间：周五 17:00
- 任务描述：法规/税率巡检、写回知识库、数据分析、生成 PPT

可粘贴 Prompt：

```text
请创建一个每周五 17:00 自动执行的合同初审周报任务：
1. 联网巡检本周法规、税率、采购合规口径变化；
2. 将变化写回知识库红线；
3. 统计本周合同合规率趋势、高频风险条款 Top5、各主体风险分布、税率和付款异常占比；
4. 生成「合同初审周报 PPT」并推送采购委员会。
```

### S03 Agent 编排

画面需要看到多步骤计划，而不是只看到最终回答。

可粘贴 Prompt：

```text
请把“企业合同初审每日流水线”拆成可执行 Agent 步骤，按依赖顺序输出：
定时触发、文档解析、联网尽调、知识库写入、知识库复核、22条规则证据、审核报告、案例归档、高风险推送。
请标明每一步输入、输出、失败降级方式。
```

### S04 合同解析与字段抽取

建议使用项目样本合同，不上传真实敏感合同。样本合同位置：

`/Users/firingj/Projects/local_crewai_demo/knowledge/sample_contract.txt`

画面需要看到：

- 已上传或粘贴合同
- 主体、金额、税率、付款比例、日期等字段抽取结果
- 说明后续会喂给规则证据节点

### S05 联网主体尽调

画面需要看到联网检索开关或检索过程，以及乙方主体画像。

可粘贴 Prompt：

```text
请联网检索合同乙方主体的工商状态、涉诉失信、经营异常、行政处罚和公开负面信息。
输出结构化主体画像：主体名称、统一社会信用代码、经营状态、司法风险、经营异常、负面舆情、建议风险等级、引用来源。
```

### S06 知识库写入

画面需要看到写入目标库名：

- `对方主体画像库`
- 或 `合同风险案例库`

可粘贴内容：

```text
请将刚才的乙方主体尽调结果沉淀到「对方主体画像库」，字段包括：主体名称、风险等级、风险来源、最近检索日期、建议处置动作。
```

### S07 @知识库 复核

画面需要同时出现 `@知识库` 和被调取的库名/结果。

可粘贴 Prompt：

```text
@知识库 请调用「对方主体画像库」和「合同风险案例库」，复核当前乙方是否存在历史高风险记录；同时调用法务红线，检查付款、税率、违约、主体资质是否触发红线。
```

### S08 数据分析

画面需要看到图表或分析结果。

可粘贴 Prompt：

```text
请基于本周合同初审结果做数据分析，并生成可视化图表：
1. 合规率周趋势；
2. 高频风险条款 Top5；
3. 各主体风险分布；
4. 税率异常占比；
5. 付款比例异常占比。
```

### S09 PPT 生成

画面需要看到 PPT 生成中或已生成的幻灯片。

可粘贴 Prompt：

```text
请生成一份「合同初审周报 PPT」，面向采购委员会，包含：
1. 本周初审概览；
2. 合规率趋势；
3. 高频风险 Top5；
4. 高风险主体观察名单；
5. 典型合同风险案例；
6. 下周治理建议。
风格商务简洁，数据口径与上一步分析一致。
```

### S10 多轮调优

画面需要体现“过程”，不要只截最终 PPT。

建议连续追问：

```text
请把第 3 页改成更适合采购委员会阅读的风险矩阵。
```

```text
请把高风险主体观察名单改成表格，并增加处置建议列。
```

```text
请把整份 PPT 的措辞从技术汇报调整为管理层决策口径。
```

## 已有本地 Demo 证据

当前仓库已有一套本地工作台演示证据，可作为“审核引擎节点”的补充材料：

- 本地截图：`/Users/firingj/Projects/local_crewai_demo/outputs/opc-demo/screenshots/`
- 本地录屏：`/Users/firingj/Projects/local_crewai_demo/outputs/opc-demo/video/local-demo-flow.webm`
- 本地 PPT：`/Users/firingj/Projects/local_crewai_demo/outputs/opc-demo/ppt/opc-contract-audit-demo.pptx`

注意：这些证明的是“工作流第 3-8 步的可体验审核引擎节点”；小浣熊端截图需要补齐定时任务、联网检索、知识库、数据分析、PPT 生成和多轮调优的真实过程。

## 当前采集状态

已完成小浣熊入口探测，但未登录账号，无法继续创建任务或进入真实工作区：

- 首页/未登录状态截图：`/Users/firingj/Projects/local_crewai_demo/outputs/xiaohuanxiong-screenshot-pack/00-office-home-or-login.png`
- 点击「任务规划」后的登录弹窗截图：`/Users/firingj/Projects/local_crewai_demo/outputs/xiaohuanxiong-screenshot-pack/00-login-required-after-plan.png`

页面可见能力入口包括：任务规划、数据分析、我的文档、知识库、生成 PPT、知识库问答、文案生成。但当前侧栏显示“登录以同步历史对话”，点击「任务规划」会弹出微信扫码/手机号登录，因此 S01-S11 需要登录后继续采集。

## 登录后采集 SOP

1. 登录小浣熊网页端或桌面端。
2. 先打开 `01-timed-task/` 对应场景，创建每日与每周定时任务，分别截 S01、S02。
3. 回到主对话，粘贴 S03 Prompt，让小浣熊输出多步骤 Agent 编排，截 S03。
4. 使用脱敏样本合同，不上传真实业务合同；样本在 `/Users/firingj/Projects/local_crewai_demo/knowledge/sample_contract.txt`。
5. 依次完成合同解析、联网尽调、知识库写入、@知识库复核、数据分析、PPT 生成、多轮调优，并按上表文件名保存。
6. 截图时尽量保留左侧导航、页面标题、输入 Prompt 和输出结果，让评委能一眼看到“能力入口 + 操作过程 + 产物”。

## 采集注意事项

- 不建议上传真实业务合同；优先使用 `knowledge/sample_contract.txt` 或脱敏样本。
- 如果需要我代操作小浣熊网页端/桌面端，需要先确认账号已登录，并明确授权我执行上传样本、创建定时任务、写入知识库、生成 PPT 等会改变账号内容的操作。
- 每张截图要保留浏览器/桌面端顶部上下文，让评委能看出这是小浣熊真实界面，而不是本地仿真图。
