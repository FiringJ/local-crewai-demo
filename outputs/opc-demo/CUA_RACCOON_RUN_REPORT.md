# CUA Driver × 办公小浣熊 OPC Demo Run Report（修订）

**Date:** 2026-06-21  
**App:** office-raccoon (`com.sensetime.desktop.raccoon`, pid 24112)  
**Driver:** user-cua-driver (Accessibility ✅, Screen Recording ✅)

---

## 为何上次标「联网未完成」？

**不是小浣熊不能联网**，而是上次全链路跑在 **「本地 Agent」** 会话里。该模式下 Agent 自身说明：

> 「当前会话未提供可用的联网搜索/浏览器工具」

因此 JSON 里出现 `online_due_diligence_status: 未完成` 是 **模式限制下的诚实标注**，不代表产品无联网能力。

**正确做法：**

| 能力 | 应使用的入口 |
| --- | --- |
| 联网尽调、@知识库、案例写回 | **云端工作台** 新建对话 |
| 本地文件、Claw 自动化 | 本地 Agent / 浣熊 Claw |
| 知识库文件入库 | **数据源 → 云上知识库 → 上传文件**（状态「已入库」） |

---

## 定时任务（2 项）

| 任务 | 调度 | 状态 |
| --- | --- | --- |
| OPC演示-每日合同初审流水线 | 每天 09:00 | ✅ 已存在 |
| OPC演示-每周合同初审周报 | 每周五（创建时时间字段为 09:00，**需手动改为 17:00**） | ⚠️ 已创建，名称/时间需你在 UI 点编辑修正 |

截图：`cua-cap1-scheduled-dual.png`（两条待执行任务）

**建议每日任务描述补充：** 每个工作日拉合同 → 云端对话尽调 → @知识库复核 → 规则 JSON → 报告 → 案例库写回。

---

## 知识库

| 项目 | 状态 |
| --- | --- |
| 云上知识库 UI | ✅ 可访问（`数据源 → 云上知识库`） |
| 已有文件 | `kb.md`（1.79 KB，已入库） |
| 应上传 | `knowledge/contract_audit_kb.md`、`knowledge/contract_audit_22_rules.md`、`outputs/opc-demo/review-response.json`（审核沉淀） |
| CUA 上传 | ⚠️ 已打开上传对话框并定位到 `knowledge/`，需在文件选择器中 **选中文件并点「打开」**（自动化未点到确认） |

本地已新增 **`knowledge/contract_audit_22_rules.md`**（22 项规则清单，供入库与 @知识库）。

---

## 六项能力 · 深化闭环 checklist

| # | 能力 | 深化要求 | 当前 |
| --- | --- | --- | --- |
| 1 | 定时任务 | 日 + 周两条 | 日 ✅ / 周 ⚠️ 时间待改 |
| 2 | 联网检索 | 云端对话 + 来源链接 + 主体画像 | 上次本地 Agent ❌ → 需云端重跑 |
| 3 | 知识库 | 上传红线+规则库；@读取；案例/画像写回 | 仅 kb.md；写回未跑 |
| 4 | 数据分析 | 粘贴 auditJson + 图表/表格 + 周度沉淀 | 本地 JSON 有；云上对话待跑 |
| 5 | 演示文稿 | 单份 6 页 + 周报 6 页 | 大纲在本地 briefing；PPT 模式待截图 |
| 6 | 对话协作 | 云端分步或一条 Agent 全链路 | 本地 Agent 7/7 仅为任务计划，非真闭环 |

---

## 推荐操作顺序（评委可复现）

1. **数据源 → 云上知识库**：上传 `contract_audit_kb.md`、`contract_audit_22_rules.md`；确认「已入库」。
2. **定时任务**：编辑周报任务为 **每周五 17:00**，名称 `OPC演示-每周合同初审周报`。
3. **云端工作台 → 新建对话**：
   - 联网尽调乙方（模块 3 prompt）
   - @知识库 复核 + 写入案例库（模块 2）
   - 数据分析粘贴 `review-response.json` 的 auditJson
   - PPT 大纲（模块 6 / WEEKLY_BRIEFING）
4. 每步截图存入 `outputs/opc-demo/screenshots/`。

Prompt 已更新：`prompts/xiaohuanxiong_core_prompts.md`（强调云端工作台、分步表）。

---

## 截图索引

| 文件 | 说明 |
| --- | --- |
| `cua-cap1-scheduled-dual.png` | 每日 + 每周两条定时任务 |
| `cua-cap1-scheduled.png` | 仅每日（旧） |
| `cua-datasource-nav.png` / `cua-cap3-kb-upload.png` | 知识库页与上传过程 |
| `cua-cap2-websearch.png` 等 | 上次本地 Agent 流水线（联网为模式限制） |
| **`cua-evidence-kb-due-diligence-supplement.png`** | **补充任务闭环证据**：知识库冲突复核 ✅、乙方联网尽调更新 ✅（10 来源）、人力节约 92%、audit JSON 13/22 通过 |
| `cua-kb-all-indexed.png` | 云上知识库 4 文件均已入库 |
| `cua-session-software-contract.png` | 首轮 7 步任务规划完整输出 |
| **`opc-full-pipeline-demo.mp4`** | **全流程录屏**（见 `recordings/full-pipeline-demo/README.md`；2026-06-21 修订：per-window 截图合成，非主屏 SCStream） |

---

## 全流程录屏（2026-06-21 修订）

| 项 | 值 |
| --- | --- |
| 交付路径 | `outputs/opc-demo/opc-full-pipeline-demo.mp4` |
| 截图包副本 | `outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/opc-full-pipeline-demo.mp4` |
| 时长 / 帧数 | 28.7s · 861 帧 @ 30fps（9 内容帧 × 2.5–4s） |
| 采集 | CuaDriver `set_recording(enabled=true, video_experimental=false)` → `turn-*/screenshot.png` |
| 合成 | ffmpeg concat；首帧 = 云上知识库 4 文件已入库；末帧 = 92% 人力节约 |
| 避免 | `video_experimental=true` 会录主屏（曾误录 Cursor IDE） |

---

## 自动化备注

- Electron 表单：任务名用 `type_text`；长正文用 AX `type_text` 或 Cmd+V。
- 定时任务频率：ComboBox 选「每周」→ 再选「周五」→ 时间 `17:00`。
- 知识库上传：需在系统「打开」面板选中文件；搜索 `contract_audit_kb.md` 后点「打开」。
