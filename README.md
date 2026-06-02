# AI 赋能的智能简历分析系统

一个面向招聘筛选场景的全栈 MVP：支持上传 PDF 简历、解析文本、提取关键信息、根据岗位 JD 进行匹配评分，并在前端展示多维度雷达图和缺失技能。

## 功能清单

- 单个 PDF 简历上传
- 多页 PDF 文本提取
- 简历文本清洗与结构化
- 姓名、电话、邮箱、地址等基本信息提取
- 求职意向、期望薪资、工作年限、学历、项目、技能关键词提取
- 岗位 JD 文本输入
- 简历与 JD 匹配评分
- 技能匹配率、经验相关性、学历匹配、项目相关、关键词覆盖五维评分
- 多维度雷达图
- 缺失技能模块
- 接入 AI 后支持语义归一化、逐条 JD 要求匹配、证据引用和缺失技能重要性
- 文件缓存，避免重复解析和重复评分
- AI 调用接口预留，无 API Key 时自动使用规则兜底
- JD URL 解析接口预留，MVP 阶段暂不启用
- 用户注册与登录
- SQLite 保存用户信息和匹配历史
- 用户可查看历史匹配记录：姓名、联系方式、岗位、匹配分数

## 技术栈

后端：

- Python 3.9+
- FastAPI
- PyMuPDF
- Pydantic
- SQLite
- OpenAI-compatible API 预留
- Redis 预留，本地文件缓存兜底

前端：

- Vite
- React
- TypeScript
- Axios
- SVG 自绘雷达图

## 项目结构

```txt
resume-ai-system/
  backend/
    app/
      api/
      schemas/
      services/
      utils/
      main.py
    requirements.txt
    .env.example
  frontend/
    src/
      components/
      App.tsx
      api.ts
      types.ts
      styles.css
    package.json
    .env.example
```

## 本地运行

### 1. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```txt
http://localhost:8000/api/health
```

API 文档：

```txt
http://localhost:8000/docs
```

### 2. 启动前端

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

默认访问：

```txt
http://localhost:5173
```

## 环境变量

后端 `backend/.env`：

```env
APP_NAME=Resume AI Analyzer
APP_ENV=local
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

AI_PROVIDER=openai_compatible
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=
AI_MODEL=gpt-4o-mini

REDIS_URL=
CACHE_DIR=.cache
DATABASE_PATH=resume_ai.db
AUTH_SECRET=please-change-this-secret
TOKEN_EXPIRE_HOURS=24
```

说明：

- `AI_API_KEY` 为空时，系统使用规则提取和规则评分。
- 如果接入通义千问、DeepSeek、Moonshot 等兼容 OpenAI API 的模型，修改 `AI_BASE_URL`、`AI_API_KEY`、`AI_MODEL` 即可。
- `REDIS_URL` 为空时，默认使用本地文件缓存。
- `DATABASE_PATH` 是 SQLite 数据库文件路径，默认保存用户和历史记录。
- `AUTH_SECRET` 用于签名登录 token，部署时必须改成随机长字符串。

前端 `frontend/.env`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## REST API

### 上传并解析简历

```http
POST /api/resumes/parse
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

字段：

```txt
file: resume.pdf
```

### 获取简历解析结果

```http
GET /api/resumes/{resume_id}
Authorization: Bearer <token>
```

### 简历匹配岗位 JD

```http
POST /api/resumes/{resume_id}/match
Content-Type: application/json
Authorization: Bearer <token>
```

请求体：

```json
{
  "job_source": {
    "source_type": "text",
    "content": "招聘 Python 后端工程师，要求熟悉 FastAPI、Redis..."
  }
}
```

返回中包含：

- `score`：综合分数
- `radar_scores`：雷达图五维评分
- `matched_keywords`：已匹配关键词
- `missing_keywords`：缺失技能 / 关键词
- `semantic_matches`：AI 逐条语义匹配证据
- `missing_skill_details`：缺失技能、重要性和原因
- `ai_summary`：分析总结

### 用户注册

```http
POST /api/auth/register
Content-Type: application/json
```

```json
{
  "username": "recruiter",
  "password": "123456"
}
```

### 用户登录

```http
POST /api/auth/login
Content-Type: application/json
```

返回 `access_token`，前端会保存到 `localStorage` 并自动带到后续请求。

### 查看匹配历史

```http
GET /api/history
Authorization: Bearer <token>
```

返回当前用户的历史记录：

```json
[
  {
    "candidate_name": "张三",
    "contact": "13800000000 / test@example.com",
    "job_title": "Python 后端工程师",
    "score": 86
  }
]
```

## 评分标准

系统采用混合评分：

```txt
最终维度分 = 规则基础分 * 40% + AI 语义评分 * 60%
综合分 =
技能匹配 * 35%
+ 经验相关 * 25%
+ 项目相关 * 20%
+ 学历匹配 * 10%
+ 关键词覆盖 * 10%
```

无 AI API Key 或 AI 调用失败时，系统自动使用规则兜底。

接入 AI 后，模型会按固定 JSON Rubric 判断：

- JD 中每条要求是否被简历证据满足
- “AI API”“大模型接口”“LLM API”等语义相近表达是否归一到同一能力项
- 匹配等级：强匹配、部分匹配、弱匹配、未匹配
- 缺失技能的重要性和原因
- 多维度评分和中文总结

## JD URL 功能预留

接口已经支持结构：

```json
{
  "job_source": {
    "source_type": "url",
    "content": "https://example.com/jobs/123"
  }
}
```

MVP 阶段返回 `501 Not Implemented`。后续可以在 `backend/app/services/job_source.py` 中增加网页抓取和正文抽取逻辑，推荐依赖：

- `httpx`
- `beautifulsoup4`
- `trafilatura`

## 阿里云函数计算 FC 部署建议

推荐使用函数计算 Web 函数或自定义运行时部署 FastAPI。

部署要点：

1. 上传 `backend` 目录。
2. 安装 `requirements.txt` 依赖。
3. 启动命令使用：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

4. 配置环境变量。
5. 将前端 `VITE_API_BASE_URL` 改为 FC 公网访问地址。

## GitHub Pages 部署前端

项目已经包含 GitHub Actions 配置：

```txt
.github/workflows/deploy-frontend.yml
```

当前前端生产 API 地址配置为：

```txt
https://resume-i-system-nzvfhfnbdd.cn-hangzhou.fcapp.run
```

部署步骤：

1. 创建 GitHub 仓库并推送本项目到 `main` 分支。
2. 进入仓库 `Settings -> Pages`。
3. `Source` 选择 `GitHub Actions`。
4. 推送后等待 `Deploy Frontend to GitHub Pages` workflow 完成。
5. 得到类似下面的前端地址：

```txt
https://你的GitHub用户名.github.io/resume-ai-system/
```

6. 回到阿里云函数计算 FC，把环境变量 `ALLOWED_ORIGINS` 改为 GitHub Pages 的 Origin：

```env
ALLOWED_ORIGINS=https://你的GitHub用户名.github.io
```

浏览器的 Origin 通常只包含协议和域名，不包含仓库路径。

如果需要手动本地构建：

```bash
cd frontend
npm install
npm run build
```

将 `frontend/dist` 部署到 GitHub Pages。也可以配置 GitHub Actions 自动部署。

## 后续升级方向

- 接入真实大模型进行更精确的信息抽取和评分
- JD URL 抓取与正文提取
- Redis 缓存
- OCR 支持扫描版 PDF
- 批量简历上传与排序
- 导出分析报告
