# AI 语音绘图

前后端分离的 AI 语音绘图工具：说出或输入画面描述，**阿里云百炼** 负责语音识别、提示词优化与图像生成，并自动保存历史记录。

**仓库**：https://github.com/continuestudycome/AIDrawLzq
**视频百度网盘地址**:通过网盘分享的文件：廖志强-AI语音绘图工具.mp4
链接: https://pan.baidu.com/s/1UX668mvTETe1urO_ExLYrQ?pwd=LZQQ 提取码: LZQQ
**BiliBili地址**：https://www.bilibili.com/video/BV13VJP6UEat/?spm_id_from=333.1387.homepage.video_card.click&vd_source=ac170834a6f3e4fa000b758817b909f5

## 功能概览

| 能力 | 说明 | 默认方案 | 费用 |
|------|------|----------|------|
| 语音输入 | 浏览器录音 → 后端识别 | 阿里云 `qwen3-asr-flash` | 按量计费 |
| 提示词优化 | 短描述扩展为中英文绘图提示词 | 阿里云 `qwen-plus` | 按量计费 |
| 图像生成 | 文本 → 图片 | 阿里云 `qwen-image-plus` | 按量计费 |
| 生成历史 | 时间、提示词、图片本地持久化 | `backend/data/history/` | 免费 |

> **一个 Key 搞定**：`DASHSCOPE_API_KEY` 同时用于语音识别、提示词优化和图像生成。

## 推荐工作流

```
点击 🎤 录音 → 停止 → 文字填入文本框
    ↓
点击「✨ 优化提示词」（生成中文展示 + 英文绘图版）
    ↓
点击「生成图像」（通常 10–60 秒）
    ↓
预览区显示结果，左侧「历史」可回看
```

> **提示**：`qwen-image-plus` 支持中英文提示词。仍建议先「优化提示词」以获得更稳定的画面描述。

## 快速开始

### 1. 后端

```powershell
cd backend

# 创建并激活虚拟环境（首次）
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量（需配置阿里云 DashScope API Key）
copy .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 启动服务
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

### 2. 前端

```powershell
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

前端通过 Vite 代理将 `/api`、`/health` 转发到后端 `8000` 端口。

> **注意**：请确保 8000 端口只运行**一个**后端进程，避免旧进程返回过期响应。修改 `backend/.env` 后需**重启后端**。

### 3. 配置阿里云 Key

编辑 `backend/.env`：

```env
DASHSCOPE_API_KEY=sk-你的真实Key
SPEECH_PROVIDER=dashscope
PROMPT_OPTIMIZER_PROVIDER=dashscope
IMAGE_PROVIDER=dashscope
DASHSCOPE_SPEECH_MODEL=qwen3-asr-flash
DASHSCOPE_CHAT_MODEL=qwen-plus
DASHSCOPE_IMAGE_MODEL=qwen-image-plus
```

### 4. 可选本地依赖（备选方案）

| 组件 | 何时需要 | 说明 |
|------|----------|------|
| 本地 Whisper | `SPEECH_PROVIDER=local` | 免费离线，需下载模型 |
| Ollama | `PROMPT_OPTIMIZER_PROVIDER=ollama` | 免费本地优化 |
| OpenAI Key | `IMAGE_PROVIDER=openai` | DALL·E 生图 |

## 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口，Ollama 启动预热
│   │   ├── config.py               # 环境变量与默认配置
│   │   ├── routers/
│   │   │   ├── draw.py             # 语音识别 / 优化 / 生图
│   │   │   ├── health.py           # 健康检查（含 provider 状态）
│   │   │   └── history.py          # 历史记录 CRUD
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   └── services/
│   │       ├── draw_pipeline.py    # 生图编排 + 历史写入
│   │       ├── local_speech_recognition.py
│   │       ├── ollama_client.py
│   │       ├── prompt_optimizer.py
│   │       ├── dashscope_image.py  # 阿里云 qwen-image-plus
│   │       ├── stable_horde_image.py
│   │       ├── image_generation.py
│   │       └── history_store.py
│   ├── tests/                      # pytest 单元测试
│   ├── scripts/
│   │   └── download_whisper_model.py
│   ├── data/history/               # 生成历史（运行时自动创建）
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.vue                 # 主界面
    │   ├── api/draw.ts             # API 封装
    │   ├── components/
    │   │   ├── HistorySidebar.vue
    │   │   └── ConfirmDialog.vue
    │   └── composables/
    │       ├── useVoiceRecording.ts
    │       └── useHistory.ts
    └── vite.config.ts
```

## 配置说明

所有配置项写在 `backend/.env`，完整示例见 `backend/.env.example`。

### 语音识别（默认：阿里云 qwen3-asr-flash）

```env
SPEECH_PROVIDER=dashscope
DASHSCOPE_SPEECH_MODEL=qwen3-asr-flash
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SPEECH_PROVIDER` | `dashscope` | `dashscope` / `local` / `openai` / `auto` |
| `DASHSCOPE_SPEECH_MODEL` | `qwen3-asr-flash` | 录音文件识别，支持中英文 |
| `DASHSCOPE_ASR_ENABLE_ITN` | `false` | 是否开启逆文本归一化 |
| `SPEECH_TIMEOUT_SECONDS` | `60` | 识别请求超时（秒） |

**本地 Whisper 备选**：

```env
SPEECH_PROVIDER=local
WHISPER_LOCAL_MODEL=base
```

### 图像生成（默认：阿里云 qwen-image-plus）

1. 登录 [阿里云百炼](https://bailian.console.aliyun.com/) 获取 API Key
2. 在 `backend/.env` 配置：

```env
IMAGE_PROVIDER=dashscope
DASHSCOPE_API_KEY=sk-your-dashscope-key
DASHSCOPE_IMAGE_MODEL=qwen-image-plus
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IMAGE_PROVIDER` | `dashscope` | `dashscope` / `openai` / `stablehorde` / `auto` |
| `DASHSCOPE_API_KEY` | （空） | 百炼 API Key，**必填** |
| `DASHSCOPE_BASE_URL` | `https://dashscope.aliyuncs.com/api/v1` | 北京地域；国际版用 `dashscope-intl.aliyuncs.com` |
| `DASHSCOPE_IMAGE_MODEL` | `qwen-image-plus` | 文生图模型 |
| `DASHSCOPE_IMAGE_SIZE` | `1328*1328` | 默认正方形；也支持 `1664*928` 等 |
| `DASHSCOPE_PROMPT_EXTEND` | `true` | 是否开启提示词智能改写 |
| `DASHSCOPE_WATERMARK` | `false` | 是否添加「Qwen-Image」水印 |
| `DASHSCOPE_MAX_WAIT_SECONDS` | `120` | 异步任务最长等待（秒） |
| `DASHSCOPE_POLL_INTERVAL` | `5` | 轮询间隔（秒） |

提供方说明：

| 值 | 说明 |
|----|------|
| `dashscope` / `qwen` | **推荐**。阿里云 qwen-image-plus，国内可用，通常 10–60 秒 |
| `auto` | 有 DashScope Key 用 qwen-image-plus，否则有 OpenAI Key 用 DALL·E，否则 Stable Horde |
| `openai` | 强制 DALL·E（需 Key） |
| `stablehorde` / `free` | Stable Horde 免费（排队慢，备选） |

**OpenAI DALL·E 示例**：

```env
OPENAI_API_KEY=sk-your-key-here
IMAGE_PROVIDER=openai
IMAGE_MODEL=dall-e-3
```

**Stable Horde 备选（免费）**：

```env
IMAGE_PROVIDER=stablehorde
STABLE_HORDE_MODELS=
```

### 提示词优化（默认：阿里云 qwen-plus）

```env
PROMPT_OPTIMIZER_PROVIDER=dashscope
DASHSCOPE_CHAT_MODEL=qwen-plus
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROMPT_OPTIMIZER_PROVIDER` | `dashscope` | `dashscope` / `ollama` / `openai` / `rules` / `auto` |
| `DASHSCOPE_CHAT_MODEL` | `qwen-plus` | 通义千问对话模型，用于扩展提示词 |
| `DASHSCOPE_CHAT_TEMPERATURE` | `0.5` | 生成温度 |
| `DASHSCOPE_CHAT_MAX_TOKENS` | `512` | 最大输出长度 |
| `PROMPT_OPTIMIZER_FALLBACK_RULES` | `true` | 云端失败时回退规则优化 |

**Ollama 本地备选**：

```env
PROMPT_OPTIMIZER_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
ollama pull qwen2.5:7b
```

### 生成历史

```env
HISTORY_ENABLED=true
HISTORY_MAX_ITEMS=100
```

历史保存在 `backend/data/history/`（JSON 元数据 + 图片文件）。响应字段 `history_saved=false` 表示图片已生成但写入历史失败。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/speech-to-text` | 上传录音，Whisper 识别为文本 |
| POST | `/api/optimize-prompt` | 优化提示词 → `optimized`（中文）+ `optimized_en`（英文） |
| POST | `/api/generate` | **主接口**：生成图像 |
| POST | `/api/transcript` | 已弃用，等价于 `/api/generate` |
| GET | `/api/history` | 历史列表 |
| GET | `/api/history/{id}/image` | 历史图片 |
| DELETE | `/api/history/{id}` | 删除一条历史 |

### `/health` 响应示例

```json
{
  "status": "ok",
  "speech_provider": "local",
  "image_provider": "stablehorde",
  "prompt_optimizer": "ollama",
  "history_enabled": true,
  "ollama_available": true
}
```

### `/api/generate` 请求示例

```json
{
  "prompt": "a cute pink pig on a sunny farm, photorealistic",
  "display_prompt": "一只可爱的粉色小猪，站在阳光下的农场草地上"
}
```

响应含 `image_url`（data URL 或历史图片地址）、`message`、`history_id`、`history_saved`。

## 常见问题

### 图片一直生成不出来？

按顺序排查：

1. **是否配置了 API Key？** 在 `backend/.env` 设置 `DASHSCOPE_API_KEY` 并 `IMAGE_PROVIDER=dashscope`，重启后端
2. **Key 是否有效？** 报错 `InvalidApiKey` 请到 [百炼控制台](https://bailian.console.aliyun.com/) 重新获取
3. **是否先优化提示词？** 建议先点「优化提示词」获得更完整描述
4. **访问 `/health`** 确认 `image_provider` 为 `dashscope`，且后端已连接

### 生成结果和描述差很多？

| 原因 | 处理 |
|------|------|
| 提示词太简短 | 先「优化提示词」，补充场景、风格、光线 |
| 智能改写不符合预期 | `.env` 设置 `DASHSCOPE_PROMPT_EXTEND=false`，自行写详细提示词 |
| 需要更高质量 | 可尝试 `qwen-image-max` 等更强模型 |

### Ollama 优化失败？

1. 确认 Ollama 运行：`ollama serve`
2. 确认模型已下载：`ollama pull qwen2.5:7b`
3. 检查 `.env` 中 `OLLAMA_MODEL` 与已拉取模型名一致
4. 访问 `/health` 查看 `ollama_available` 是否为 `true`

### 语音识别没反应？

1. 右上角应显示「**后端已连接**」
2. 确认 `DASHSCOPE_API_KEY` 已配置且 `SPEECH_PROVIDER=dashscope`
3. 点击 🎤 开始 → 说话 → **再点 ■ 停止**（需点两次）
4. 录音时长不超过 5 分钟，文件建议小于 10MB

### 预览区裂图？

后端会将远程图片下载为 **data URL** 再返回。若仍裂图，检查 `DASHSCOPE_API_KEY` 是否有效，或查看后端日志中的下载错误。

## 开发与测试

### 运行单元测试

```powershell
cd backend
.\.venv\Scripts\pip.exe install pytest
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

覆盖 provider 解析、规则优化、JSON 解析等核心逻辑。

### 第三方依赖

**后端**：FastAPI、Uvicorn、faster-whisper、httpx、pydantic-settings、pytest

**前端**：Vue 3、Vite、TypeScript

**外部 AI 服务**：

| 服务 | 用途 | 是否需要 Key |
|------|------|--------------|
| [阿里云百炼 DashScope](https://bailian.console.aliyun.com/) | qwen-image-plus 文生图 | 是 |
| [Ollama](https://ollama.com/) | 本地提示词优化 | 否 |
| [OpenAI](https://platform.openai.com/) | Whisper / DALL·E（可选） | 是 |
| [Stable Horde](https://stablehorde.net/) | 免费文本生图（备选） | 否 |

## 开发进度

- [x] 占位图 → OpenAI DALL·E → Pollinations → Stable Horde → **阿里云 qwen-image-plus**
- [x] 本地 Whisper 语音识别（MediaRecorder + faster-whisper）
- [x] Ollama 提示词优化（中英文双版本）
- [x] 生成历史（侧边栏、删除确认、本地持久化）
- [x] 架构重构（`draw_pipeline`、前端 composables、`/api/generate` 主接口、health 增强、pytest）
- [x] Stable Horde 连接重试（备选方案）
- [x] 接入阿里云 DashScope `qwen-image-plus` 文生图

## 下一步

- WebSocket 流式识别与生图进度
- 异步生图任务（避免长时间阻塞 HTTP 请求）
