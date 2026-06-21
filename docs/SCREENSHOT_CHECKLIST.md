# 小浣熊截图证据清单

> 提交作品时，建议至少放入 **5 张截图 + 1 段录屏**。  
> 重点不是只展示最终结果，而是让评委看到：任务怎么创建、怎么运行、怎么读取知识库、怎么产出分析和周报。

---

## 提交前自检

- [ ] 演示文稿和作品简介都明确写出“办公小浣熊”
- [ ] 至少 1 张定时任务截图，证明不是一次性聊天
- [ ] 至少 1 张任务运行截图或录屏，证明任务可以触发
- [ ] 至少 1 张知识库上传或读取截图，证明经验能沉淀
- [ ] 至少 1 张对方公司风险查询截图；如果当前没有联网结果，要如实保留降级说明
- [ ] 至少 1 张数据分析或周报生成截图，证明能复盘
- [ ] 至少 1 张多轮修改截图，证明你不是只拿一次回答当结果

---

## 最小必备截图组合

| 编号 | 截图内容 | 证明什么 |
| --- | --- | --- |
| S1 | 小浣熊桌面端首页或工作台入口 | 作品确实以小浣熊为主角 |
| S2 | “每日合同初审流水线”定时任务创建成功 | 工作流可定时运行 |
| S3 | 定时任务右侧菜单出现“立刻运行” | 任务可手动触发，便于评委理解 |
| S4 | 任务运行中或运行完成后的摘要 | 不是只写了方案，确实跑过 |
| S5 | 知识库文件上传成功或被引用 | 法务红线和案例能复用 |
| S6 | 合同字段抽取或固定检查结果 | 检查清单能给小浣熊提供证据 |
| S7 | 数据分析结果或周报生成过程 | 每周复盘闭环成立 |

---

## 已整理好的证据位置

| 证据 | 文件位置 | 建议用途 |
| --- | --- | --- |
| 定时任务待执行 | `outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/01-schedule-task-ready.png` | 演示文稿第 7 页 |
| 立刻运行菜单 | `outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/02-task-menu-run-option.png` | 演示“可触发” |
| 任务运行中 | `outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/03-task-running-manual-trigger.png` | 封面或运行证据页 |
| 任务完成摘要 | `outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/06-task-complete-summary-updated.png` | 证明运行后有结果 |
| 任务运行录屏 | `outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/desktop-raccoon-task-run-verified.mov` | 提交材料包必放 |
| **全流程录屏（推荐）** | `outputs/opc-demo/opc-full-pipeline-demo.mp4`（副本：`outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/opc-full-pipeline-demo.mp4`） | 知识库 + 定时立刻运行 + 历史完成 + 云端 7 步闭环 + 人力节约 92%；**SCStream 连续主屏视频**（1987 帧，见 `recordings/full-pipeline-live/`） |
| 截图包总说明 | `outputs/xiaohuanxiong-screenshot-pack/MANIFEST.md` | 解释每张图的含义 |
| 知识库冲突复核 + 联网尽调补充 | `outputs/opc-demo/screenshots/cua-evidence-kb-due-diligence-supplement.png` | S5/S6：@知识库 三组冲突表、乙方尽调带来源、人力节约 92%、audit JSON 口径 |

---

## 逐能力截图建议

| 小浣熊能力 | 应该截什么 | 画面里最好露出什么 |
| --- | --- | --- |
| 定时任务 | 创建任务、任务列表、立刻运行、运行中状态 | 任务名称、触发时间、任务摘要 |
| 联网检索 | 查询对方公司公开风险 | 联网开关、查询结果、来源链接；若失败，保留失败说明 |
| 知识库 | 上传法务红线、读取历史案例、写入风险案例 | 文件名、引用标记、写入确认 |
| 数据分析 | 合同审核结果统计 | 通过率、高风险项、趋势或排行 |
| 演示文稿 | 周报大纲生成或页面生成过程 | 周报标题、页码、正在生成的页面 |
| 对话协作 | 同一任务前后两轮修改 | 第一轮问题、第二轮修改要求、结果变化 |

---

## 讲述顺序建议

1. 先展示小浣熊入口：评委知道作品形态是什么。
2. 再展示定时任务：说明它是持续工作流，不是单次问答。
3. 展示任务运行录屏：证明它能被触发。
4. 展示合同字段和固定检查：说明风险判断有依据。
5. 展示知识库：说明经验能沉淀。
6. 展示数据分析和周报：说明管理层能看到复盘结果。

---

## 如实说明

当前材料已经证明了小浣熊桌面端任务创建、手动触发、运行中状态和完成摘要。云端工作台会话 `cua-evidence-kb-due-diligence-supplement.png` 已展示联网尽调（检索 10 个网页来源）、知识库规则冲突复核与 `review-response.json` 校准口径；若乙方名称与工商登记不完全一致，应如实保留「需人工复核」说明，不要写成已线下核实主体。
