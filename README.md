# Ontology Management System (本体管理系统)

这是一个全栈本体管理系统，支持 ZIP 包上传、解析、查看和管理。

## 技术栈 (Tech Stack)

*   **后端 (Backend)**: Python 3.10+, FastAPI, SQLAlchemy, SQLite
*   **前端 (Frontend)**: Vue 3, Vite, Element Plus, Axios
*   **数据存储**:
    *   元数据: SQLite (`backend/app/ontology.db`)
    *   文件存储: 本地磁盘 (`backend/data/ontology_storage/`)

## 目录结构 (Structure)

```text
onto_manage/
├── backend/                # 后端代码
│   ├── app/                # 应用源码
│   │   ├── main.py         # FastAPI 入口
│   │   ├── manager.py      # 核心逻辑
│   │   ├── ...
│   └── data/               # 数据存储 (自动生成)
├── frontend/               # 前端代码 (Vue 3)
│   ├── src/
│   │   ├── App.vue         # 主界面
│   │   └── ...
│   └── vite.config.js      # Vite 配置 (含 API 代理)
├── run.py                  # 后端启动脚本
└── README.md
```

## 快速开始 (Quick Start)

### 1. 环境准备

确保已安装 Python 3.10+ 和 Node.js 16+。

### 2. 后端启动

```bash
# 安装依赖
pip install -r backend/requirements.txt

# 启动服务 (默认端口 8000)
python run.py
```

### 3. 前端启动 (开发模式)

```bash
cd frontend

# 安装依赖
npm install
npm install axios element-plus

# 启动开发服务器 (默认端口 5173)
npm run dev
```

前端会自动代理 API 请求到 `http://127.0.0.1:8003`。
访问浏览器显示的 URL (通常是 `http://localhost:5173`) 开始使用。

## 功能说明

1.  **上传本体**: 支持拖拽上传 ZIP 文件。系统会自动解压并防止 Zip Slip 漏洞。
2.  **列表查看**: 查看所有已上传的本体及其状态。
3.  **详情查看**: 点击"查看详情"，浏览包内的 Markdown 文件结构，并点击文件查看内容预览。
6.  **Webhook 订阅**:
    *   支持订阅 `ontology.uploaded` 事件。
    *   **Payload 增强**: 推送请求采用 `multipart/form-data` 格式，包含 JSON 元数据和原始 ZIP 文件。
    *   **投递日志**: 记录每次 Webhook 的投递状态（成功/失败、响应码、错误信息）。
    *   **状态弹窗**: 上传后自动弹出投递进度窗口，实时展示各个订阅方的推送结果。
7.  **本体更新**: 
    *   支持同名本体覆盖上传。
    *   前端提供 **覆盖确认** 提示，防止误操作。
    *   支持点击列表中的 **"更新"** 按钮直接替换旧版本。
8.  **Markdown 渲染**: 详情页使用 `markdown-it` + `github-markdown-css` 渲染富文本内容。

## API 文档

启动后端后，访问 `http://127.0.0.1:8003/docs` 查看 Swagger API 文档。 (默认端口已改为 8003)

## 集成指南

关于如何对接 Webhook 和使用 SDK，请参考 [docs/integration_guide.md](docs/integration_guide.md)。
