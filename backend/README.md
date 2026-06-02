# Backend

FastAPI 后端服务，负责 PDF 解析、信息提取、岗位匹配和缓存。

## 运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 核心接口

- `GET /api/health`
- `POST /api/resumes/parse`
- `GET /api/resumes/{resume_id}`
- `POST /api/resumes/{resume_id}/match`
