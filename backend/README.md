# AI Voice Draw — Backend

FastAPI 后端服务，提供语音识别与图像生成 API。

## 启动

```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：http://127.0.0.1:8000/docs

前端项目位于同级目录 `../frontend/`。
