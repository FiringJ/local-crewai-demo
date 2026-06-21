# OPC 全流程连续录屏（live）

**成片：** `../../opc-full-pipeline-demo.mp4`（约 66s @ 30fps，无音频，3024×1964）

## 录屏章节（按成片顺序）

| 顺序 | 画面 | 证明能力 | 验证帧 |
| --- | --- | --- | --- |
| 1 | 云上知识库 · 4 文件已入库 | 知识库上传与索引 | `verify/first.png` |
| 2 | 定时任务 · 日/周两条待执行 | 定时任务 | `verify/t10.png` |
| 3 | 每日流水线 · **立刻运行** 菜单 | 任务可手动触发 | turn-00003 |
| 4 | 历史 · 流水线运行记录 | 运行有结果 | `verify/t40.png` |
| 5 | 软件服务合同初审报告会话 | 云端任务规划闭环 | `verify/last.png` |
| 6 | 任务规划模式 · 7 步 pipeline | 分步执行可视化 | turn-00013 |
| 7 | 尽调补充 · **92% 人力节约** | 联网、知识库、数据分析 | `verify/last.png` |

## 技术备注

- **采集方式：** CuaDriver `recording start --video-experimental` → 主屏 SCStream 连续 H.264（30fps，无音频，无光标）。
- **前台准备：** 录制前 `osascript` 隐藏 Cursor，激活 `office-raccoon`；录制期间隐藏 Cua Driver 窗口。
- **成片渲染：** `cua-driver recording render … --no-zoom`（连续视频，无 click-zoom 特效）。
- **目标应用：** office-raccoon（pid 24112，window 468），云端工作台。
- **逐步截图：** 本目录 `turn-00001/` … 供调试；**交付物以 `recording.mp4` / 渲染 MP4 为准**。
- **验证：** `verify/first.png` = 知识库首帧；`verify/last.png` = 92% 人力节约末帧；均为办公小浣熊 UI（非 Cursor）。

## 复现

```bash
# 1. 启动 CuaDriver daemon
open -n -g -a CuaDriver --args serve

# 2. 隐藏 Cursor，激活小浣熊
osascript -e 'tell application "System Events" to set visible of process "Cursor" to false'
osascript -e 'tell application "office-raccoon" to activate'

# 3. 开始连续录屏
cua-driver recording start outputs/opc-demo/recordings/full-pipeline-live --video-experimental

# 4. 导航全流程（可用 run_demo_v2.py）
python3 outputs/opc-demo/recordings/full-pipeline-live/run_demo_v2.py

# 5. 停止并渲染
cua-driver recording stop
cua-driver recording render outputs/opc-demo/recordings/full-pipeline-live \
  --output outputs/opc-demo/opc-full-pipeline-demo.mp4 --no-zoom

# 6. 恢复 Cursor
osascript -e 'tell application "System Events" to set visible of process "Cursor" to true'
```
