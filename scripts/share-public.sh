#!/usr/bin/env bash
# 一键把本机服务暴露到公网（零安装，使用 macOS 自带 ssh + localhost.run）
#
#   用法：
#     bash scripts/share-public.sh            # 默认端口 7860
#     PORT=8000 bash scripts/share-public.sh  # 自定义端口
#
#   说明：
#   - 脚本会前台常驻，关掉终端 / 电脑休眠后公网链接即失效。
#   - 公网域名形如 https://xxxxxxxx.lhr.life，每次重启会变。
#   - Ctrl+C 同时停止隧道与后端。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-7860}"
cd "$ROOT"

cleanup() {
  echo ""
  echo "正在停止隧道与后端…"
  [[ -n "${TUNNEL_PID:-}" ]] && kill "$TUNNEL_PID" 2>/dev/null || true
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 1) 启动后端（若该端口未在监听）
if curl -fsS -o /dev/null "http://127.0.0.1:${PORT}/api/config" 2>/dev/null; then
  echo "✅ 后端已在 127.0.0.1:${PORT} 运行，复用现有进程。"
else
  echo "🚀 启动后端 (crew_gui) 于 0.0.0.0:${PORT} …"
  uv run crew_gui --no-open --host 0.0.0.0 --port "${PORT}" > /tmp/crew_gui.log 2>&1 &
  BACKEND_PID=$!
  for _ in $(seq 1 30); do
    if curl -fsS -o /dev/null "http://127.0.0.1:${PORT}/api/config" 2>/dev/null; then
      echo "✅ 后端就绪。"
      break
    fi
    sleep 1
  done
  if ! curl -fsS -o /dev/null "http://127.0.0.1:${PORT}/api/config" 2>/dev/null; then
    echo "❌ 后端启动失败，查看 /tmp/crew_gui.log"
    tail -20 /tmp/crew_gui.log || true
    exit 1
  fi
fi

# 2) 开公网隧道
echo "🌐 建立公网隧道（localhost.run）…"
echo "------------------------------------------------------------------"
echo "下面输出里形如  https://xxxxxxxx.lhr.life  的地址即为公网访问链接。"
echo "把它发给别人即可访问。保持本终端开启，链接才有效。"
echo "------------------------------------------------------------------"
ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -R 80:localhost:"${PORT}" nokey@localhost.run &
TUNNEL_PID=$!
wait "$TUNNEL_PID"
