# 云端部署指南

> **Render 要绑信用卡？** 见 [`docs/DEPLOY_NO_CARD.md`](DEPLOY_NO_CARD.md) — 推荐 **Hugging Face Spaces**（免绑卡、固定链接）或 **Cloudflare 隧道**（最快）。

本项目已配置 **Docker 一键部署**。GitHub 仓库：https://github.com/FiringJ/local-crewai-demo

---

## 免绑卡（推荐）

| 方案 | 绑卡 | 链接稳定性 | 说明 |
|------|------|------------|------|
| [Hugging Face Spaces](DEPLOY_NO_CARD.md#方案-1hugging-face-spaces推荐--固定公网链接--免绑卡) | 否 | 高 | 固定 `*.hf.space` 域名 |
| [Cloudflare 隧道](DEPLOY_NO_CARD.md#方案-2cloudflare-临时隧道最快--本机在线即可) | 否 | 低 | 本机开着才有 |

详细步骤：**[`docs/DEPLOY_NO_CARD.md`](DEPLOY_NO_CARD.md)**

---

## 部署前准备

1. 把代码推到 **GitHub**（Render / Railway 都从 Git 拉取）
2. 确认本地能跑通（可选）：
   ```bash
   docker build -t contract-audit .
   docker run --rm -p 7860:7860 -e PORT=7860 -e DEEPSEEK_API_KEY=你的key contract-audit
   ```
3. 准备 LLM 环境变量（至少一个）：
   - `DEEPSEEK_API_KEY` + `MODEL=deepseek/deepseek-chat`（开发调试）
   - 或 `SENSENOVA_API_KEY` + `MODEL=openai/SenseChat-5` + `BASE_URL=https://api.sensenova.cn/compatible-mode/v2`（比赛推荐）

**切勿**把 API Key 提交进 Git，只在平台控制台填环境变量。

---

## 方案 A：Render（部分地区强制绑卡）

> 若出现 **Add Card** 弹窗且不想绑卡，请改用 [`DEPLOY_NO_CARD.md`](DEPLOY_NO_CARD.md) 中的 Hugging Face 或 Cloudflare 方案。

### 推荐：Web Service（免 Blueprint / 常免绑卡）

1. 打开 [https://render.com](https://render.com) 注册，用 GitHub 登录  
2. 点击 **New +** → **Web Service**（不要选 Blueprint）  
3. 连接 GitHub 仓库：`FiringJ/local-crewai-demo`  
4. 配置：
   - **Runtime**: Docker  
   - **Instance Type**: **Free**  
   - **Health Check Path**: `/api/config`  
5. 在 **Environment** 添加变量，例如：
   ```
   DEEPSEEK_API_KEY=sk-...
   MODEL=deepseek/deepseek-chat
   HOST=0.0.0.0
   CREWAI_DISABLE_TELEMETRY=true
   CREWAI_TRACING_ENABLED=false
   ```
7. 点击 **Create Web Service**，等待构建（约 5～10 分钟，含前端 npm build）  
8. 部署完成后访问：`https://你的服务名.onrender.com`

### 备选：Blueprint（可能需要绑卡）

若使用 **Blueprint** 并出现 Add Card 弹窗，说明 Render 要求身份验证。可 **Cancel** 后改用上文 Web Service 方式，或见下文「完全不想绑卡」方案。

### Render 注意事项

- 免费档一段时间无访问会**休眠**，首次打开需等 30～60 秒唤醒  
- 免费档 HTTP 请求有**超时限制**，「小浣熊全链路」若超过 30 秒可能失败；公网 Demo 建议默认用 **「仅规则引擎」**，或升级付费档  
- 健康检查：`/api/config` 返回 200 即正常  

---

## 方案 B：Railway（试用额度，操作简单）

1. 打开 [https://railway.app](https://railway.app) 注册，用 GitHub 登录  
2. **New Project** → **Deploy from GitHub repo** → 选择本仓库  
3. Railway 会自动识别根目录 `Dockerfile` 和 `railway.toml`  
4. 进入服务 → **Variables**，添加：
   ```
   DEEPSEEK_API_KEY=sk-...
   MODEL=deepseek/deepseek-chat
   HOST=0.0.0.0
   ```
   （`PORT` 由 Railway 自动注入，无需手填）  
5. **Settings** → **Networking** → **Generate Domain**，获得公网 URL  
6. 打开生成的 `https://xxxx.up.railway.app` 即可体验  

### Railway 注意事项

- 按用量计费，新账号通常有试用额度；注意控制台余额  
- Agent 全链路审核约 20～60 秒，Railway 一般比 Render 免费档更适合长请求  
- 日志在 **Deployments → View Logs** 查看  

---

## 完全不想绑信用卡？

以下方案 **0 绑卡**，适合比赛 Demo / 临时分享链接。

### 方案 C：Cloudflare 临时隧道（推荐，5 分钟）

本机先启动服务：

```bash
cd /Users/firingj/Projects/local_crewai_demo
uv run crew_gui --no-open --port 7860
```

另开终端安装并运行隧道（无需注册信用卡）：

```bash
# 未安装时：brew install cloudflared
cloudflared tunnel --url http://127.0.0.1:7860
```

终端会输出公网地址，例如 `https://xxxx.trycloudflare.com`，发给评委即可。  
**注意**：你电脑需保持开机；关闭终端后链接失效。

### 方案 D：局域网演示

同一 WiFi：`uv run crew_gui --no-open --host 0.0.0.0 --port 7860`  
别人访问 `http://你的电脑IP:7860`。

---

## 环境变量参考

| 变量 | 必填 | 说明 |
|------|------|------|
| `PORT` | 自动 | 平台注入，应用已支持 |
| `HOST` | 建议 `0.0.0.0` | 监听所有网卡 |
| `DEEPSEEK_API_KEY` | 二选一 | DeepSeek |
| `SENSENOVA_API_KEY` | 二选一 | 办公小浣熊 / SenseNova |
| `MODEL` | 建议 | 如 `deepseek/deepseek-chat` |
| `BASE_URL` | SenseNova 时需要 | 商汤兼容接口地址 |

---

## 公网 Demo 安全建议

当前应用**没有登录鉴权**，任何人打开链接都能消耗你的 API 额度。建议：

1. 比赛演示时优先展示 **「仅规则引擎」**（不耗 LLM）  
2. 全链路模式仅在答辩/内测时开启  
3. 不要把带 Key 的链接发到公开社群；用完可在平台旋转 Key  

---

## 故障排查

| 现象 | 处理 |
|------|------|
| 页面 502 / 无法访问 | 看平台构建日志；确认 Docker build 成功 |
| 只有旧版 UI | 构建时 `frontend/dist` 未生成；检查 Dockerfile 前端构建阶段 |
| 审核秒回 +「已回退」 | 环境变量 Key 未配置或错误 |
| Render 请求超时 | 改用「仅规则引擎」或换 Railway / 付费档 |

本地验证健康检查：

```bash
curl https://你的域名/api/config
```

应返回 JSON，含 `competition`、`providers` 等字段。
