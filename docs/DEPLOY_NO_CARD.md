# 免绑信用卡部署指南

Render / Railway 在部分地区或新账号会**强制绑信用卡**（哪怕选 Free）。若你不想绑卡，请用下面两种方案。

---

## 方案 1：Hugging Face Spaces（推荐 · 固定公网链接 · 免绑卡）

免费 Docker 空间：2 vCPU、16GB RAM，**不需要信用卡**。与本项目 `Dockerfile` 已对齐（端口 7860）。

### 步骤

1. 注册 [https://huggingface.co](https://huggingface.co)（邮箱即可，无需绑卡）

2. 创建 Space：**New Space**
   - Space name：例如 `contract-audit-demo`
   - SDK：**Docker**
   - Visibility：Public
   - Hardware：**CPU basic · Free**

3. 在 Space 页面 → **Settings → Repository secrets** 添加：
   ```
   DEEPSEEK_API_KEY=sk-你的key
   MODEL=deepseek/deepseek-chat
   HOST=0.0.0.0
   CREWAI_DISABLE_TELEMETRY=true
   CREWAI_TRACING_ENABLED=false
   ```

4. 本地关联并推送代码（把 `YOUR_USER` 换成你的 HF 用户名）：

   ```bash
   cd /Users/firingj/Projects/local_crewai_demo

   # 在 huggingface.co/settings/tokens 创建 Write token
   git remote add space https://huggingface.co/spaces/YOUR_USER/contract-audit-demo

   # 首次推送（覆盖 Space 默认文件）
   git push space main --force
   ```

   提示输入 HF 用户名 + **Access Token**（不是登录密码）。

5. 回到 Space 页面看 **Building** → **Running**，访问：
   ```
   https://YOUR_USER-contract-audit-demo.hf.space
   ```
   或 Space 页右上角的 **Open app**。

### 注意

- 免费 Space **48 小时无访问会休眠**，首次打开需等 1～2 分钟唤醒  
- 可用 [UptimeRobot](https://uptimerobot.com)（免费）每 5 分钟 ping `https://xxx.hf.space/api/config` 减少休眠  
- Agent 全链路审核约 20～60 秒，HF 比 Render 免费档更适合长请求  
- **切勿**把 API Key 写进代码；只用 Repository secrets  

---

## 方案 2：Cloudflare 临时隧道（最快 · 本机在线即可）

适合今天就要发链接、不想注册新平台。

```bash
# 终端 1：启动应用
cd /Users/firingj/Projects/local_crewai_demo
uv run crew_gui --no-open --port 7860

# 终端 2：安装并开隧道（无需信用卡）
brew install cloudflared
cloudflared tunnel --url http://127.0.0.1:7860
```

复制输出的 `https://xxxx.trycloudflare.com` 发给评委。  
**电脑关机或关终端后链接失效。**

---

## 不推荐（需绑卡）

| 平台 | 说明 |
|------|------|
| **Render** | Blueprint / Web Service 均可能要求 Add Card |
| **Fly.io** | 新账号通常必须绑卡 |
| **Railway** | 部分账号可免绑卡，但不稳定 |

---

## 比赛 Demo 建议

1. **长期链接**：Hugging Face Spaces  
2. **临时答辩**：Cloudflare 隧道 + 本机  
3. **公网演示**：默认用「仅规则引擎」，避免 Key 被刷额度  

GitHub 仓库：https://github.com/FiringJ/local-crewai-demo
