# OPC 全流程录屏说明

**成片：** `../../opc-full-pipeline-demo.mp4`（约 29 秒，无音频，3024×1718 @ 30fps）

## 录屏章节（按成片顺序）

| 顺序 | 画面 | 证明能力 | 来源 |
| --- | --- | --- | --- |
| 1 | 云上知识库 · 4 文件已入库 | 知识库上传与索引 | `screenshots/cua-kb-all-indexed.png` |
| 2 | 定时任务 · 日/周两条待执行 | 定时任务 | `turn-00010/screenshot.png` |
| 3 | 每日流水线 · **立刻运行** 菜单 | 任务可手动触发 | `turn-00012/screenshot.png` |
| 4 | 执行中 · 手动触发运行中 | 流水线已启动 | `turn-00013/screenshot.png` |
| 5 | 历史 · 流水线 1 分钟前 | 运行有结果 | `turn-00014/screenshot.png` |
| 6 | 历史 · 查看输出（自动化工作流） | 定时任务产出可读 | `turn-00016/screenshot.png` |
| 7 | 软件服务合同初审报告会话 | 云端任务规划闭环 | `turn-00018/screenshot.png` |
| 8 | 任务规划模式 · 7 步 pipeline | 分步执行可视化 | `turn-00021/screenshot.png` |
| 9 | 尽调补充 · 冲突表 / 联网 / **92% 人力节约** | 联网、知识库、数据分析 | `turn-00022/screenshot.png` |

## 技术备注

- **采集方式：** CuaDriver `set_recording` 且 `video_experimental=false`。每步 action 写入 `turn-NNNNN/screenshot.png`，为 **目标 pid 前台窗口** 的 per-window 截图，**不是**主屏 SCStream。
- **成片合成：** 从上述 PNG 按 `assembly/manifest.json` 时长拼接（ffmpeg），输出 `opc-full-pipeline-demo.mp4`。**请勿**使用 `video_experimental=true` 的 `recording.mp4` 作为交付物（会录到 Cursor 等主屏前台应用）。
- **目标应用：** office-raccoon（pid 24112，window 468），云端工作台。
- **逐步截图：** 本目录 `turn-00001/` … `turn-00022/`；合成帧见 `assembly/frame_*.png`。
- **验证：** `assembly/verify/first.png` = 知识库首帧；`assembly/verify/last.png` = 92% 人力节约末帧；均为办公小浣熊 UI。

## 复现

```bash
# 1. 启动 CuaDriver daemon
open -n -g -a CuaDriver --args serve

# 2. MCP 调用 set_recording(enabled=true, video_experimental=false, output_dir=本目录)
# 3. 在办公小浣熊云端工作台按章节顺序导航并 click/scroll
# 4. set_recording(enabled=false)
# 5. 按 assembly/manifest.json 用 ffmpeg 合成（见 assembly/ 脚本或手动 concat）
```
