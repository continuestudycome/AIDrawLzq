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
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 加载 `.env` 配置 |

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
| [Stable Horde](https://stablehorde.net/) | 免费文本生成图像（社区算力） | 步骤 4 修复 | 否（匿名 Key） |

## 原创功能

以下为项目自行实现的功能（非第三方库直接提供）：

| 模块 | 说明 |
|------|------|
| 语音录音流程 | 前端使用浏览器 `MediaRecorder` 采集麦克风，录音结束后上传后端 |
| 语音识别编排 | 后端 `app/services/speech_recognition.py` 封装 Whisper API 调用、错误处理与配置读取 |
| 图像生成编排 | 后端 `app/services/image_generation.py` 统一调度 OpenAI / Stable Horde / Pollinations |
| Stable Horde 免费绘图 | 后端 `app/services/stable_horde_image.py` 提交异步任务、轮询并下载图片 |
| 图片转 data URL | 后端 `app/services/image_fetch.py` 将远程图片转为 data URL，避免浏览器裂图 |
| Pollinations URL 构建 | 后端 `app/services/pollinations_image.py` 构建 Pollinations 图片地址（服务已收费时自动跳过） |
| 占位图像生成 | 后端 `app/services/placeholder_image.py` 在免费服务超时/不可用时返回 SVG 占位图 |
| API 编排 | 前端 `src/api/draw.ts` 封装健康检查、语音识别、图像生成请求及错误解析 |
| 开发代理 | Vite 将 `/api`、`/health` 代理到后端，前后端分离本地联调 |

## 开发进度

- [x] **步骤 1**：后端占位图像生成（`/api/transcript`、`/api/generate` 返回可预览 SVG）
- [x] **步骤 2**：接入 OpenAI Whisper 语音识别（`/api/speech-to-text`）
- [x] **步骤 3**：接入 OpenAI DALL·E 图像生成（`/api/transcript`、`/api/generate`）
- [x] **步骤 4**：接入 Pollinations 免费图像生成
- [x] **步骤 4 修复**：Pollinations 收费后改用 Stable Horde，后端转 data URL 修复裂图
- [ ] **步骤 5**：接入浏览器免费语音识别（Web Speech API）

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

## 语音识别配置（步骤 2）

在 `backend/.env` 中设置：

```env
OPENAI_API_KEY=sk-your-key-here
SPEECH_LANGUAGE=zh
```

可选配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | 兼容 OpenAI 格式的代理地址 |
| `SPEECH_MODEL` | `whisper-1` | Whisper 模型 |
| `SPEECH_LANGUAGE` | `zh` | 语言提示，提升中文识别准确率 |
| `SPEECH_TIMEOUT_SECONDS` | `60` | 请求超时（秒） |

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

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/speech-to-text` | 上传语音，Whisper 识别为文本 |
| POST | `/api/transcript` | 根据文本生成图像（返回 data URL 或图片地址） |
| POST | `/api/generate` | 根据提示词生成图像 |

## 常见问题

### 显示「图像已生成」但预览区裂图？

Pollinations 免费 API 已返回 **402 需付费**。请改用：

```env
IMAGE_PROVIDER=stablehorde
```

并重启后端。新版会将图片下载为 **data URL** 再返回，避免浏览器无法加载外链。

### 生成很慢？

Stable Horde 免费匿名队列可能需要 **1-3 分钟**甚至更久，属正常现象。可在 [stablehorde.net](https://stablehorde.net/register) 注册获取专属 Key 提升优先级。

### 语音识别报错？

语音识别仍依赖 OpenAI Whisper，无 Key 时会失败。可手动输入提示词生成图像，或等待步骤 5 接入浏览器免费语音识别。

## 下一步

- 步骤 5：接入浏览器免费语音识别（Web Speech API）
- 增加 WebSocket 流式识别与生成进度
