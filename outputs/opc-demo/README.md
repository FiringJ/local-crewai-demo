# OPC Demo 演示包

本目录用于向评委说明作品形态：办公小浣熊负责持续运营工作流，本地 Demo 负责演示每日流水线中的审核引擎节点。

## 主要文件

- `ppt/opc-contract-audit-demo.pptx`：8 页可编辑演示 PPT。
- `ppt/preview-contact-sheet.png`：PPT 预览拼图。
- `video/local-demo-flow.webm`：本地审核节点录屏。
- `screenshots/01-home.png` 到 `screenshots/07-rules.png`：本地 Demo 截图证据。
- `review-response.json`：样本合同审核接口返回结果。
- **`opc-full-pipeline-demo.mp4`**：办公小浣熊桌面端 **全流程连续录屏**（约 66s @ 30fps，3024×1964，知识库 → 定时任务立刻运行 → 历史记录 → 云端会话闭环 + 92% 人力节约）。由 CuaDriver **SCStream 主屏连续视频**（`video_experimental=true`）采集，`recording render --no-zoom` 输出；旁注见 `recordings/full-pipeline-live/README.md`。

## 本地复现

```bash
uv run crew_gui --no-open
```

打开 `http://127.0.0.1:7860`，上传 `knowledge/realistic_software_service_contract.txt`，选择「仅规则引擎（离线演示）」后点击「开始审核」。

如需跑小浣熊/SenseNova 全链路，在 `.env` 配置 `SENSENOVA_API_KEY`，并选择「小浣熊全链路（推荐）」。

## 提交提醒

本目录截图证明本地审核节点可运行。最终提交仍建议按 `docs/SCREENSHOT_CHECKLIST.md` 在小浣熊网页端补拍定时任务、联网检索、知识库存取、数据分析、PPT 生成和多轮调优截图。
