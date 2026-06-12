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
| [httpx](https://www.python-httpx.org/) | 调用 OpenAI Whisper 语音识别 API |
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

| 服务 | 用途 | 步骤 |
|------|------|------|
| [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text) | 语音转文字 | 步骤 2 |

## 原创功能

以下为项目自行实现的功能（非第三方库直接提供）：

| 模块 | 说明 |
|------|------|
| 语音录音流程 | 前端使用浏览器 `MediaRecorder` 采集麦克风，录音结束后上传后端 |
| 语音识别编排 | 后端 `app/services/speech_recognition.py` 封装 Whisper API 调用、错误处理与配置读取 |
| 占位图像生成 | 后端 `app/services/placeholder_image.py` 根据提示词动态生成 SVG 占位预览图 |
| API 编排 | 前端 `src/api/draw.ts` 封装健康检查、语音识别、图像生成请求 |
| 开发代理 | Vite 将 `/api`、`/health` 代理到后端，前后端分离本地联调 |

## 开发进度

- [x] **步骤 1**：后端占位图像生成（`/api/transcript`、`/api/generate` 返回可预览 SVG）
- [x] **步骤 2**：接入 OpenAI Whisper 语音识别（`/api/speech-to-text`）
- [ ] 步骤 3：接入真实 AI 图像生成

## 项目结构

```
.
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── main.py        # FastAPI 入口
│   │   ├── config.py      # 配置
│   │   ├── routers/       # API 路由
│   │   ├── schemas/       # 请求/响应模型
│   │   └── services/      # 业务服务（语音识别、占位图等）
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

# 复制环境变量并填写 OPENAI_API_KEY
copy .env.example .env

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/speech-to-text` | 上传语音，Whisper 识别为文本 |
| POST | `/api/transcript` | 根据文本生成图像 |
| POST | `/api/generate` | 根据提示词生成图像 |

## 下一步

- 接入图像生成 API（如 Stable Diffusion、DALL·E 等）
- 增加 WebSocket 流式识别与生成进度
