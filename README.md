# AI 语音绘图

前后端分离的 AI 语音绘图工具：说出或输入画面描述，本地 Whisper 识别语音，Ollama 优化提示词，Stable Horde 免费生图，并自动保存历史记录。

**仓库**：https://github.com/continuestudycome/AIDrawLzq

## 功能概览

| 能力 | 说明 | 默认方案 | 费用 |
|------|------|----------|------|
| 语音输入 | 浏览器录音 → 后端识别 | 本地 faster-whisper | 免费 |
| 提示词优化 | 短描述扩展为中英文绘图提示词 | Ollama `qwen2.5:7b` | 免费（本地） |
| 图像生成 | 文本 → 图片 | Stable Horde | 免费（排队） |
| 生成历史 | 时间、提示词、图片本地持久化 | `backend/data/history/` | 免费 |

## 推荐工作流

```
点击 🎤 录音 → 停止 → 文字填入文本框
    ↓
点击「✨ 优化提示词」（生成中文展示 + 英文绘图版）
    ↓
点击「生成图像」（使用英文版，等待 1–3 分钟）
    ↓
预览区显示结果，左侧「历史」可回看
```

> **重要**：Stable Horde 免费模型主要理解**英文关键词**。请尽量先优化提示词，不要直接用中文生图。

## 快速开始

### 1. 后端

```powershell
cd backend

# 创建并激活虚拟环境（首次）
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量（无 API Key 也可使用 Stable Horde + 本地 Whisper）
copy .env.example .env

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

### 3. 可选依赖

| 组件 | 何时需要 | 安装方式 |
|------|----------|----------|
| Whisper 模型 | 首次语音识别 | `python scripts/download_whisper_model.py` |
| Ollama | 提示词优化 | [ollama.com](https://ollama.com/) → `ollama pull qwen2.5:7b` |
| OpenAI Key | DALL·E / Whisper API | 在 `.env` 配置 `OPENAI_API_KEY` |

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

### 语音识别（默认：本地 Whisper，免费）

```env
SPEECH_PROVIDER=local
WHISPER_LOCAL_MODEL=base
HUGGINGFACE_ENDPOINT=https://hf-mirror.com
HUGGINGFACE_HUB_DISABLE_SSL=true
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SPEECH_PROVIDER` | `local` | `local` / `openai` / `auto` |
| `WHISPER_LOCAL_MODEL` | `base` | `tiny`（快）/ `base`（推荐）/ `small` |
| `WHISPER_LOCAL_MODEL_PATH` | （空） | 本地模型目录，跳过在线下载 |
| `HUGGINGFACE_ENDPOINT` | `https://hf-mirror.com` | Hugging Face 国内镜像 |
| `HUGGINGFACE_HUB_DISABLE_SSL` | `true` | 解决 Windows SSL 证书问题 |

**预下载 Whisper 模型（推荐）**：

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\download_whisper_model.py
```

完成后在 `.env` 设置脚本输出的 `WHISPER_LOCAL_MODEL_PATH`。

### 图像生成（默认：Stable Horde，免费）

```env
IMAGE_PROVIDER=stablehorde
STABLE_HORDE_MODELS=
STABLE_HORDE_STEPS=28
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IMAGE_PROVIDER` | `stablehorde` | `stablehorde` / `openai` / `auto` / `pollinations` |
| `STABLE_HORDE_API_KEY` | `0000000000` | 匿名 Key；[注册](https://stablehorde.net/register) 后可换专属 Key 提升优先级 |
| `STABLE_HORDE_MAX_WAIT_SECONDS` | `180` | 免费队列最长等待（秒） |
| `STABLE_HORDE_STEPS` | `28` | 生成步数 |
| `STABLE_HORDE_MODELS` | （留空） | 指定模型名，逗号分隔；**留空**使用任意可用 worker（匿名 Key 推荐） |
| `STABLE_HORDE_CONNECT_TIMEOUT_SECONDS` | `30` | 连接超时（秒） |
| `STABLE_HORDE_REQUEST_TIMEOUT_SECONDS` | `90` | 单次请求超时（秒） |
| `STABLE_HORDE_NEGATIVE_PROMPT` | （内置） | 负面提示词，过滤低质量结果 |

提供方说明：

| 值 | 说明 |
|----|------|
| `stablehorde` / `free` | **推荐**。Stable Horde 免费生成，排队约 1–3 分钟 |
| `auto` | 有 OpenAI Key 用 DALL·E，否则走 Stable Horde |
| `openai` | 强制 DALL·E（需 Key） |
| `pollinations` | 已返回 402 需付费，不推荐 |

**OpenAI DALL·E 示例**：

```env
OPENAI_API_KEY=sk-your-key-here
IMAGE_PROVIDER=openai
IMAGE_MODEL=dall-e-3
```

### 提示词优化（默认：Ollama，免费）

```env
PROMPT_OPTIMIZER_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_KEEP_ALIVE=30m
OLLAMA_WARMUP_ON_STARTUP=true
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROMPT_OPTIMIZER_PROVIDER` | `ollama` | `ollama` / `openai` / `rules` |
| `OLLAMA_MODEL` | `qwen2.5:7b` | 推荐；追求速度可换 `qwen2.5:3b` |
| `OLLAMA_NUM_PREDICT` | `256` | 最大生成长度 |
| `OLLAMA_CACHE_ENABLED` | `true` | 相同输入命中缓存 |
| `PROMPT_OPTIMIZER_FALLBACK_RULES` | `true` | Ollama 失败时回退规则优化 |

安装 Ollama 并拉取模型：

```powershell
ollama pull qwen2.5:7b
ollama serve   # 通常安装后已自动运行
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

1. **是否先点了「优化提示词」？** 中文直出效果差且易失败，应使用英文 `optimized_en` 生图
2. **是否等待足够久？** 免费队列通常需 **1–3 分钟**，界面会显示「正在生成图像…」
3. **Stable Horde 连接失败**（`All connection attempts failed`）  
   - 服务器在境外，国内网络可能不稳定  
   - 检查能否访问 https://stablehorde.net  
   - 换网络、开代理，或稍后重试（后端已内置自动重试）  
   - 或改用 OpenAI DALL·E
4. **排队超时**（`>180 秒`）  
   - 确认 `.env` 中 `STABLE_HORDE_MODELS` **留空**（不要锁 `Deliberate` 等热门模型）  
   - 或注册专属 Key 提升优先级  
   - 可适当增大 `STABLE_HORDE_MAX_WAIT_SECONDS`

### 生成结果和描述差很多？

| 原因 | 处理 |
|------|------|
| 未优化，直接用中文生图 | 先「优化提示词」，确认英文版含主体词（如 `pig`、`cat`） |
| 指定热门模型排队过久 | 清空 `STABLE_HORDE_MODELS` |
| 提示词太抽象 | 补充场景、风格、光线等具体描述 |
| 免费模型能力有限 | 注册 Stable Horde Key 或配置 OpenAI DALL·E |

### Ollama 优化失败？

1. 确认 Ollama 运行：`ollama serve`
2. 确认模型已下载：`ollama pull qwen2.5:7b`
3. 检查 `.env` 中 `OLLAMA_MODEL` 与已拉取模型名一致
4. 访问 `/health` 查看 `ollama_available` 是否为 `true`

### 语音识别没反应？

1. 右上角应显示「**后端已连接**」
2. 点击 🎤 开始 → 说话 → **再点 ■ 停止**（需点两次）
3. 首次使用需下载 Whisper 模型，请耐心等待
4. 若报 SSL 错误，设置 `HUGGINGFACE_ENDPOINT` 并预下载模型（见上文）

### 预览区裂图？

Pollinations 已返回 402 需付费。请确认：

```env
IMAGE_PROVIDER=stablehorde
```

后端会将远程图片下载为 **data URL** 再返回，避免浏览器无法加载外链。

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
| [Stable Horde](https://stablehorde.net/) | 免费文本生图 | 否（匿名 Key） |
| [Ollama](https://ollama.com/) | 本地提示词优化 | 否 |
| [OpenAI](https://platform.openai.com/) | Whisper / DALL·E | 是 |
| [Pollinations.ai](https://pollinations.ai/) | 文本生图 | 已收费，不推荐 |

## 开发进度

- [x] 占位图 → OpenAI DALL·E → Pollinations → **Stable Horde** 免费生图
- [x] 本地 Whisper 语音识别（MediaRecorder + faster-whisper）
- [x] Ollama 提示词优化（中英文双版本）
- [x] 生成历史（侧边栏、删除确认、本地持久化）
- [x] 架构重构（`draw_pipeline`、前端 composables、`/api/generate` 主接口、health 增强、pytest）
- [x] Stable Horde 连接重试、超时配置优化

## 下一步

- WebSocket 流式识别与生图进度
- 异步生图任务（避免长时间阻塞 HTTP 请求）
