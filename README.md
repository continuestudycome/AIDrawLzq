# AI 语音绘图

前后端分离的 AI 语音绘图工具：前端 Vue 3 负责录音与展示，后端 FastAPI 负责语音识别与图像生成。

## 第三方依赖

### 后端（Python）

| 库 | 用途 |
|----|------|
| [FastAPI](https://fastapi.tiangolo.com/) | Web API 框架 |
| [Uvicorn](https://www.uvicorn.org/) | ASGI 服务器 |
| [python-multipart](https://github.com/Kludex/python-multipart) | 上传语音文件解析 |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | 环境变量与配置管理 |
| [httpx](https://www.python-httpx.org/) | 调用 OpenAI、Stable Horde 等 HTTP 服务 |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 本地 Whisper 语音识别（免费） | 步骤 6 |

### 前端（Node.js）

| 库 | 用途 |
|----|------|
| [Vue 3](https://vuejs.org/) | 前端 UI 框架 |
| [Vite](https://vite.dev/) | 开发与构建工具 |
| [TypeScript](https://www.typescriptlang.org/) | 类型检查 |
| [@vitejs/plugin-vue](https://github.com/vitejs/vite-plugin-vue) | Vite 的 Vue 插件 |
| [vue-tsc](https://github.com/vuejs/language-tools) | Vue 单文件组件类型检查 |

### 外部 AI 服务

| 服务 | 用途 | 步骤 | 是否需要 Key |
|------|------|------|--------------|
| [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text) | 语音转文字 | 步骤 2 | 是 |
| [OpenAI Images API (DALL·E)](https://platform.openai.com/docs/api-reference/images) | 文本生成图像 | 步骤 3 | 是 |
| [Pollinations.ai](https://pollinations.ai/) | 文本生成图像（已收费 402，不推荐） | 步骤 4 | 否（已不可用） |
| [Ollama](https://ollama.com/) | 本地大模型提示词优化 | 步骤 7 | 否（本地运行） |

## 原创功能

以下为项目自行实现的功能（非第三方库直接提供）：

| 模块 | 说明 |
|------|------|
| 语音录音与识别 | 前端 MediaRecorder 录音，停止后上传后端本地 Whisper 识别为文字 |
| 本地 Whisper 识别 | 后端 `app/services/local_speech_recognition.py`，免费离线，国内可用 |
| 图像生成编排 | 后端 `app/services/image_generation.py` 统一调度 OpenAI / Stable Horde / Pollinations |
| Stable Horde 免费绘图 | 后端 `app/services/stable_horde_image.py` 提交异步任务、轮询并下载图片 |
| 图片转 data URL | 后端 `app/services/image_fetch.py` 将远程图片转为 data URL，避免浏览器裂图 |
| Pollinations URL 构建 | 后端 `app/services/pollinations_image.py` 构建 Pollinations 图片地址（服务已收费时自动跳过） |
| 占位图像生成 | 后端 `app/services/placeholder_image.py` 在免费服务超时/不可用时返回 SVG 占位图 |
| 提示词优化 | 默认调用 **Ollama** 本地大模型，生成中文展示版与英文绘图版；失败时可回退规则优化 |
| 生成历史 | 后端 `app/services/history_store.py` 保存时间、中英文提示词与图片到 `backend/data/history/` |
| API 编排 | 前端 `src/api/draw.ts` 封装健康检查、语音识别、提示词优化、图像生成、历史记录请求 |
| 开发代理 | Vite 将 `/api`、`/health` 代理到后端，前后端分离本地联调 |

## 开发进度

- [x] **步骤 1**：后端占位图像生成（`/api/transcript`、`/api/generate` 返回可预览 SVG）
- [x] **步骤 2**：接入 OpenAI Whisper 语音识别（`/api/speech-to-text`）
- [x] **步骤 3**：接入 OpenAI DALL·E 图像生成（`/api/transcript`、`/api/generate`）
- [x] **步骤 4**：接入 Pollinations 免费图像生成
- [x] **步骤 4 修复**：Pollinations 收费后改用 Stable Horde，后端转 data URL 修复裂图
- [x] **提示词优化**：新增「优化提示词」按钮，扩展简短描述提升生成准确度
- [x] **步骤 6**：后端本地 Whisper 免费语音识别（录音 → 停止 → 文字填入文本框）
- [x] **生成历史**：自动保存生成时间、提示词与图片，支持查看与删除
- [x] **Ollama 提示词优化**：调用本地大模型扩展用户输入为中英文绘图提示词

## 项目结构

```
.
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── main.py        # FastAPI 入口
│   │   ├── config.py      # 配置
│   │   ├── routers/       # API 路由
│   │   ├── schemas/       # 请求/响应模型
│   │   └── services/      # 业务服务（语音识别、图像生成等）
│   ├── requirements.txt
│   └── .env.example
└── frontend/              # Vue 3 前端
    ├── src/
    ├── vite.config.ts
    └── package.json
```

## 快速开始

### 1. 后端

```bash
cd backend

# 激活虚拟环境（Windows）
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量（无 API Key 也可使用 Stable Horde 免费绘图）
copy .env.example .env

# 启动服务
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API 文档：http://127.0.0.1:8000/docs

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

前端已通过 Vite 代理将 `/api` 和 `/health` 转发到后端 `8000` 端口。

> **注意**：请确保 8000 端口只运行一个后端进程，避免旧进程返回过期响应。

## 语音识别（步骤 6，免费推荐）

**录音 → 停止 → 文字自动填入下方文本框**，不依赖浏览器语音识别，国内可用。

| 项目 | 说明 |
|------|------|
| 技术 | 前端 MediaRecorder 录音 + 后端 faster-whisper 本地识别 |
| 费用 | 免费，无需 API Key |
| 网络 | 首次运行需下载模型（约 150MB），之后可离线识别 |
| 用法 | 点击 🎤 开始录音 → 说话 → 再点 ■ 停止 → 文字出现在文本框 |

### 配置

```env
SPEECH_PROVIDER=local
WHISPER_LOCAL_MODEL=base
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SPEECH_PROVIDER` | `local` | `local` / `openai` / `auto` |
| `WHISPER_LOCAL_MODEL` | `base` | 模型：`tiny`（快）/ `base`（推荐）/ `small` |
| `WHISPER_LOCAL_LANGUAGE` | `zh` | 识别语言 |
| `WHISPER_LOCAL_DEVICE` | `cpu` | 运行设备 |
| `WHISPER_LOCAL_COMPUTE_TYPE` | `int8` | 量化类型，CPU 推荐 int8 |
| `HUGGINGFACE_ENDPOINT` | `https://hf-mirror.com` | Hugging Face 国内镜像 |
| `HUGGINGFACE_HUB_DISABLE_SSL` | `true` | 解决 Windows SSL 证书问题 |
| `WHISPER_LOCAL_MODEL_PATH` | （空） | 本地已下载模型目录，跳过在线下载 |

首次识别会自动下载 Whisper 模型，可能需要几分钟。

**若报 SSL 证书错误**，按顺序尝试：

1. 确认 `backend/.env` 已设置镜像（并重启后端）：

```env
HUGGINGFACE_ENDPOINT=https://hf-mirror.com
HUGGINGFACE_HUB_DISABLE_SSL=true
```

2. **推荐**：手动预下载模型（避免首次识别时在线拉取）：

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\download_whisper_model.py
```

下载完成后在 `.env` 添加（脚本会打印路径）：

```env
WHISPER_LOCAL_MODEL_PATH=D:/七牛云/backend/models/faster-whisper-base
```

### 首次使用（安装）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
.\.venv\Scripts\python.exe scripts\download_whisper_model.py
```

### 可选：OpenAI Whisper API

```env
SPEECH_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

## 图像生成配置（步骤 3 / 4）

**无 API Key 推荐配置**：使用 Stable Horde 免费服务（匿名 Key，无需注册）。

```env
# 推荐：Stable Horde 免费服务
IMAGE_PROVIDER=stablehorde

# 或有 OpenAI Key 时
OPENAI_API_KEY=sk-your-key-here
IMAGE_PROVIDER=openai
IMAGE_MODEL=dall-e-3
```

提供方说明：

| 值 | 说明 |
|----|------|
| `stablehorde` / `free` | **推荐**。Stable Horde 免费生成，排队约 1-3 分钟 |
| `auto` | 有 OpenAI Key 用 DALL·E，否则走 Stable Horde |
| `openai` | 强制使用 DALL·E（需 Key） |
| `pollinations` | Pollinations（`image.pollinations.ai` 已返回 402 需付费，不推荐） |

可选配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IMAGE_PROVIDER` | `auto` | `auto` / `openai` / `stablehorde` / `free` / `pollinations` |
| `IMAGE_API_KEY` | （复用 `OPENAI_API_KEY`） | 单独指定图像生成 Key |
| `IMAGE_MODEL` | `dall-e-3` | OpenAI 模型 |
| `IMAGE_QUALITY` | `standard` | DALL·E 3 画质 |
| `STABLE_HORDE_API_KEY` | `0000000000` | 匿名 Key；注册后可换专属 Key 提升优先级 |
| `STABLE_HORDE_MAX_WAIT_SECONDS` | `180` | 免费队列最长等待（秒） |
| `STABLE_HORDE_STEPS` | `20` | 生成步数 |
| `POLLINATIONS_BASE_URL` | `https://image.pollinations.ai` | Pollinations 地址（已收费） |
| `IMAGE_TIMEOUT_SECONDS` | `120` | HTTP 请求超时（秒） |

## 提示词优化配置（Ollama）

默认使用本地 **Ollama** 将用户输入的实体词/短描述扩展为中英文绘图提示词。

### 安装与启动 Ollama

1. 安装 [Ollama](https://ollama.com/)
2. 拉取模型（推荐中文能力较好的模型）：

```powershell
ollama pull qwen2.5:7b
```

3. 确认服务运行（安装后通常自动启动）：

```powershell
ollama serve
```

### 配置

```env
PROMPT_OPTIMIZER_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROMPT_OPTIMIZER_PROVIDER` | `ollama` | `ollama` / `openai` / `rules` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API 地址 |
| `OLLAMA_MODEL` | `qwen2.5:7b` | 使用的本地模型 |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | 请求超时（秒） |
| `PROMPT_OPTIMIZER_FALLBACK_RULES` | `true` | Ollama 失败时回退规则优化 |

### 用法

输入简短描述（如「猪」「赛博朋克风格的猫」）→ 点击 **「✨ 优化提示词」** → 输入框显示中文说明，英文版用于生成图像。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/speech-to-text` | 上传录音，本地 Whisper 或 OpenAI 识别为文本 |
| POST | `/api/optimize-prompt` | 优化提示词，返回 `optimized`（中文展示）与 `optimized_en`（英文绘图） |
| POST | `/api/transcript` | 根据文本生成图像（返回 data URL 或图片地址） |
| POST | `/api/generate` | 根据提示词生成图像 |
| GET | `/api/history` | 获取生成历史列表 |
| GET | `/api/history/{id}/image` | 获取历史记录中的图片 |
| DELETE | `/api/history/{id}` | 删除一条历史记录 |

## 常见问题

### 提示词太短，生成结果不对？

点击 **「✨ 优化提示词」**，系统会调用 Ollama 本地大模型将简短描述扩展为详细的中英文绘图提示词，提升 Stable Horde 等模型的理解准确度。需先安装并启动 Ollama。

### Ollama 优化失败？

1. 确认 Ollama 已运行：`ollama serve`
2. 确认模型已下载：`ollama pull qwen2.5:7b`
3. 检查 `backend/.env` 中 `OLLAMA_MODEL` 与已拉取的模型名一致

### 显示「图像已生成」但预览区裂图？

Pollinations 免费 API 已返回 **402 需付费**。请改用：

```env
IMAGE_PROVIDER=stablehorde
```

并重启后端。新版会将图片下载为 **data URL** 再返回，避免浏览器无法加载外链。

### 生成很慢？

Stable Horde 免费匿名队列可能需要 **1-3 分钟**甚至更久，属正常现象。可在 [stablehorde.net](https://stablehorde.net/register) 注册获取专属 Key 提升优先级。

### 语音识别没反应？

1. 确认**后端已启动**（右上角显示「后端已连接」）
2. 点击 🎤 开始 → 说话 → **再点 ■ 停止**（必须点两次）
3. 等待「正在识别语音…」，文字会填入下方文本框
4. 首次使用需下载 Whisper 模型，请耐心等待

## 下一步

- 增加 WebSocket 流式识别与生成进度
