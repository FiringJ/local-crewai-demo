#!/usr/bin/env bash
# 推送代码到 Hugging Face Space: FiringJ/contract-audit-demo
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SPACE_REPO="https://huggingface.co/spaces/FiringJ/contract-audit-demo"

cd "$ROOT"

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "请先设置 HF Token（在 https://huggingface.co/settings/tokens 创建 Write 权限）："
  echo "  export HF_TOKEN=hf_xxxxxxxx"
  exit 1
fi

if ! git remote get-url space &>/dev/null; then
  git remote add space "$SPACE_REPO"
fi

echo "正在推送到 Hugging Face Space..."
git push "https://FiringJ:${HF_TOKEN}@huggingface.co/spaces/FiringJ/contract-audit-demo" main --force

echo ""
echo "推送完成。打开：https://huggingface.co/spaces/FiringJ/contract-audit-demo"
echo "构建约 5～10 分钟，完成后访问：https://firingj-contract-audit-demo.hf.space"
