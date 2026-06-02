# AI Powered Resume Analysis System

AI 赋能的智能简历分析系统。项目面向招聘筛选场景，支持 PDF 简历上传、文本解析、关键信息提取、岗位 JD 语义匹配、多维度评分、缺失技能分析、用户登录和历史记录查看。

线上前端地址：

```txt
https://boyazhang54.github.io/AI_powered_resume_system/
```

后端服务部署在阿里云函数计算 FC：

```txt
https://resume-i-system-nzvfhfnbdd.cn-hangzhou.fcapp.run
```

## 项目架构

本项目采用前后端分离架构：

```txt
用户浏览器
  -> GitHub Pages 前端
  -> 阿里云函数计算 FC 后端
  -> PDF 解析 / AI 模型调用 / SQLite / 缓存
```

核心目录结构：

```txt
AI_powered_resume_system/
  backend/
    app/
      api/          # REST API：认证、简历解析、匹配历史
      schemas/      # Pydantic 请求和响应模型
      services/     # PDF 解析、AI 调用、评分、缓存、数据库
      utils/
      main.py       # FastAPI 入口
    requirements.txt
    .env.example
  frontend/
    src/
      components/   # 雷达图等组件
      App.tsx       # 页面主逻辑
      api.ts        # 后端 API 封装
      types.ts
    package.json
  .github/workflows/
    deploy-frontend.yml
  README.md
```

后端主要流程：

```txt
PDF 上传
  -> PyMuPDF 提取多页文本
  -> 文本清洗
  -> AI/规则抽取简历信息
  -> 输入岗位 JD
  -> AI 语义匹配 + 规则评分
  -> 返回 JSON 结果
  -> 保存匹配历史
```

前端主要流程：

```txt
登录/注册
  -> 上传 PDF
  -> 查看简历结构化信息
  -> 输入 JD
  -> 查看综合评分、雷达图、缺失技能、语义匹配证据
  -> 查看历史记录
```

## 技术选型

后端：

- Python 3.10
- FastAPI：提供 RESTful API
- PyMuPDF：解析 PDF 简历文本，支持多页 PDF
- Pydantic：定义结构化请求和响应模型
- SQLite：保存用户信息和匹配历史
- OpenAI-compatible API：接入 DeepSeek / Qwen / OpenAI 兼容模型
- 本地文件缓存：缓存简历解析和匹配结果
- Redis：已预留接口，生产环境可替换本地缓存

前端：

- React
- TypeScript
- Vite
- Axios
- SVG 自绘雷达图
- GitHub Pages 自动部署

部署：

- 后端：阿里云函数计算 FC
- 前端：GitHub Pages
- AI 模型：DeepSeek API，兼容其他 OpenAI-compatible 服务

## 功能说明

已实现功能：

- 用户注册与登录
- PDF 简历上传和解析
- 简历关键信息提取：姓名、电话、邮箱、地址、技能、学历、项目经历等
- 岗位 JD 文本输入
- AI 语义匹配评分
- 多维度雷达图评估
- 缺失技能分析
- 语义匹配证据展示
- 匹配历史记录：姓名、联系方式、岗位、匹配分数
- 缓存机制：避免相同简历和 JD 重复计算

预留能力：

- JD URL 解析接口
- Redis 缓存
- OCR 解析扫描版 PDF
- 批量简历上传和排序
- 导出分析报告

## AI 评分逻辑

系统采用“规则基础分 + AI 语义评分”的混合评分方式。

综合分权重：

```txt
综合分 =
技能匹配 * 35%
+ 经验相关 * 25%
+ 项目相关 * 20%
+ 学历匹配 * 10%
+ 关键词覆盖 * 10%
```

接入 AI 后，模型会输出结构化 JSON，用于：

- 将“AI API”“大模型接口”“LLM API”等相近表达归一化为同一能力项
- 逐条判断 JD 要求是否被简历证据满足
- 给出匹配等级：强匹配、部分匹配、弱匹配、未匹配
- 给出缺失技能、重要性和原因
- 生成中文分析总结

如果 AI API 调用失败，系统会自动回退到规则评分，保证基础功能可用。

## 数据库设计

MVP 阶段使用 SQLite，数据库文件默认由环境变量 `DATABASE_PATH` 指定。

主要存储：

- 用户信息：用户名、密码哈希、创建时间
- 匹配历史：用户 ID、简历 ID、候选人姓名、联系方式、岗位名称、匹配分数、分析模式、创建时间

说明：

- 密码不会明文存储，使用 PBKDF2 哈希。
- 当前 SQLite 适合 MVP 演示；生产环境建议迁移到阿里云 RDS / PolarDB。

## 后端 API

认证：

```http
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

简历：

```http
POST /api/resumes/parse
GET  /api/resumes/{resume_id}
POST /api/resumes/{resume_id}/match
```

历史记录：

```http
GET /api/history
```

健康检查：

```http
GET /api/health
```

## 本地运行

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：

```txt
http://localhost:8000/api/health
http://localhost:8000/docs
```

### 前端

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

访问：

```txt
http://localhost:5173
```

前端本地环境变量：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 部署方式

### 后端部署到阿里云函数计算 FC

后端使用 FastAPI Web 服务方式部署。

关键配置：

```txt
运行环境：Python 3.10
监听端口：9000
启动方式：bash bootstrap
```

`bootstrap` 中启动 FastAPI：

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${FC_SERVER_PORT:-9000}"
```

FC 环境变量示例：

```env
AI_BASE_URL=https://api.deepseek.com/v1
AI_API_KEY=your_api_key
AI_MODEL=deepseek-chat
ALLOWED_ORIGINS=https://boyazhang54.github.io
DATABASE_PATH=/tmp/resume_ai.db
CACHE_DIR=/tmp/.cache
AUTH_SECRET=please-change-this-secret
TOKEN_EXPIRE_HOURS=24
```

说明：

- `.env` 不上传到 GitHub，也不打包到部署包中。
- API Key 应配置在阿里云 FC 环境变量中。
- FC 中的 `/tmp` 是临时存储，生产环境建议使用 RDS 保存用户和历史记录。

### 前端部署到 GitHub Pages

前端使用 GitHub Actions 自动部署。

工作流文件：

```txt
.github/workflows/deploy-frontend.yml
```

构建时注入后端地址：

```env
VITE_API_BASE_URL=https://resume-i-system-nzvfhfnbdd.cn-hangzhou.fcapp.run
```

GitHub Pages 地址：

```txt
https://boyazhang54.github.io/AI_powered_resume_system/
```

部署后，需要在阿里云 FC 中配置 CORS：

```env
ALLOWED_ORIGINS=https://boyazhang54.github.io
```

## 使用说明

1. 打开前端页面。
2. 注册或登录账号。
3. 上传单个 PDF 简历。
4. 等待系统解析简历并展示结构化信息。
5. 粘贴岗位 JD 文本。
6. 点击“开始匹配”。
7. 查看综合匹配分、雷达图、缺失技能和语义匹配证据。
8. 进入“历史记录”查看过往匹配结果。

## 安全说明

- `.env`、数据库文件、缓存文件、依赖目录不会提交到 GitHub。
- API Key 通过部署平台环境变量配置。
- 前端不会保存阿里云 AccessKey。
- 登录 token 存储在浏览器 `localStorage`，适合 MVP；生产环境可升级为 HttpOnly Cookie。

## 后续优化方向

- 使用 RDS 替代 SQLite，提升持久化能力
- 接入 Redis / Tair 缓存
- 支持扫描版 PDF OCR
- 支持批量简历分析和排序
- 支持 JD URL 自动抓取
- 支持导出 PDF / Word 分析报告
