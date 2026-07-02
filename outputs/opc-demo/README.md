# OPC Demo 提交材料包（复赛版）

本目录存放提交与路演直接使用的材料。历史过程产物已移至仓库根 `_archive/`。

## 主要文件

- `ppt/opc-xiaohuanxiong-workflow-submission.pptx`：复赛 12 页演示 PPT（源：`ppt/xiaohuanxiong-slides.html`，构建：`node ppt/assemble-deck.mjs && node ppt/html-to-pptx.mjs`；预览图：`ppt/xiaohuanxiong-preview/`）。
- `合同初审持续运营工作流-附件-提交.zip`：提交附件三件套（录屏 / Prompt / 截图），解包版在同名目录。
- `screenshots/`：本地审核台截图证据。
- `review-response.json`：样本合同审核接口返回结果。
- `agent-prompt-ready.txt` / `schedule-weekly-task-prompt.txt`：小浣熊会话与定时任务 Prompt。
- 小浣熊桌面端全流程录屏（66s）：`outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/opc-full-pipeline-demo.mp4`。

## 本地复现

```bash
uv run crew_gui --no-open
```

打开 `http://127.0.0.1:7860`，上传 `knowledge/realistic_software_service_contract.txt`，选择「仅规则引擎（离线演示）」后点击「开始审核」。

如需跑小浣熊/SenseNova 全链路，在 `.env` 配置 `SENSENOVA_API_KEY`，并选择「小浣熊全链路（推荐）」。

## 路演待办

见 `docs/COMPETITION_GUIDE.md` 第四节（Skill 配置、飞书截图补拍、彩排口径）。
