# OntoHub - Enterprise Ontology Management System

**OntoHub** 是一个企业级本体包管理平台，旨在为上下游系统提供统一、版本化的本体模型分发服务。它支持本体的上传、版本管理、生命周期控制以及基于 Webhook 的事件通知机制。

![OntoHub UI](frontend/public/vite.svg)

## 核心特性 (Key Features)

### 1. 多版本管理 (Versioning)
*   **系列编码 (Series ID)**：引入 `Code` 字段作为本体的唯一标识，跨版本保持不变 (e.g., `auth-module`)。
*   **语义化版本控制**：自动为同名/同码本体维护多个版本（v1, v2, ...）。
*   **版本切换**：支持随时查看和回溯历史版本。
*   **生命周期状态**：
    *   **Active (启用)**：当前生效的主版本，供下游系统消费。
    *   **Deprecated (弃用)**：过时版本，保留用于历史兼容。

### 2. 自动化分发 (Webhook Integration)
*   **事件驱动**：当新版本本体被 **"启用 (Activate)"** 时，自动触发 Webhook。
*   **智能推送**：
    *   支持配置订阅特定本体名称（Filter）。
    *   推送 Payload 包含完整的元数据及 ZIP 包下载链接。
*   **可观测性**：
    *   实时记录推送日志（成功/失败状态、响应码）。
    *   提供重试机制和交付详情查看。

### 3. 安全与完整性 (Security & Integrity)
*   **删除保护**：
    *   **Active 保护**：正在启用的版本（Active）禁止删除。
    *   **使用中保护**：被下游系统通过 Webhook 成功接收且未更新的版本，禁止删除，防止破坏依赖。
*   **完整性校验**：上传时自动检查 ZIP 包结构安全性（防止 Zip Slip）。

### 4. 本体管理与重析 (Management & Re-parsing)
*   **元数据动态更新**：支持随时修改本体的显示名称、描述以及默认解析模板（影响未来版本）。
*   **按需重新解析**：
    *   **版本隔离**：重析操作仅针对当前选定版本，不影响历史快照。
    *   **模板覆盖**：支持在重析时指定临时模板，用于算法对比或修复解析错误。
---
### 5. 可视化与探索 (Visualization)
*   **多维视图**：提供文件树、知识图谱、实体列表、关系列表等多个维度的本体探索体验。
*   **响应式对话框**：全局采用适配大屏的响应式布局，支持跨设备无缝缩放。
*   **富文本渲染**：集成 `markdown-it`，提供友好的文档阅读体验。

---

## 技术栈 (Tech Stack)

*   **后端 (Backend)**: 
    *   Python 3.10+
    *   **FastAPI**: 高性能异步 Web 框架
    *   **SQLAlchemy**: ORM 数据库管理
    *   **SQLite**: 轻量级元数据存储
*   **前端 (Frontend)**: 
    *   **Vue 3**: 渐进式 JavaScript 框架
    *   **Vite**:并通过极速构建工具
    *   **Element Plus**: 企业级 UI 组件库
    *   **Axios**: HTTP 客户端

---

## 快速开始 (Quick Start)

### 1. 环境准备
确保您的环境已安装：
*   Python 3.10+
*   Node.js 18+
*   Git

### 2. 后端启动
```bash
cd onto_manage

# 1. 安装依赖
pip install -r backend/requirements.txt

# 2. 启动服务 (自动初始化数据库)
# 服务将运行在 http://127.0.0.1:8003
python run.py
```

### 3. 前端启动
```bash
cd onto_manage/frontend

# 1. 安装依赖
npm install

# 2. 开发模式启动 (热重载)
npm run dev

# 3. 生产环境构建
# 构建产物将生成在 frontend/dist，后端会自动托管
npm run build
```

---

## 目录结构 (Project Structure)

```text
onto_manage/
├── backend/
│   ├── app/
│   │   ├── services/       # 业务逻辑层 (OntologyService, WebhookService)
│   │   ├── repositories/   # 数据访问层 (CRUD)
│   │   ├── routers/        # API 路由定义
│   │   ├── models.py       # SQLAlchemy 数据模型
│   │   └── schemas.py      # Pydantic 数据验证模型
│   ├── data/               # SQLite 数据库与文件存储
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Vue 组件
│   │   ├── App.vue         # 主应用入口
│   │   └── ...
│   └── vite.config.js      # 前端构建配置
├── docs/                   # 项目文档
├── run.py                  # 项目启动脚本 (含 uvicorn 配置)
└── README.md
```

## API 接口文档 (Interactive API Docs)

本项目利用 FastAPI 的特性自动生成交互式 API 文档。启动后端服务后，您可以直接在浏览器中查看参数说明并进行接口调试：

*   **Swagger UI (推荐)**: [http://127.0.0.1:8003/docs](http://127.0.0.1:8003/docs)
*   **ReDoc**: [http://127.0.0.1:8003/redoc](http://127.0.0.1:8003/redoc)

> [!TIP]
> Swagger UI 支持在线发送请求，是调试“本体重析”和“Webhook 配置”等接口的最快方式。

## 贡献指南
1.  Fork 本仓库
2.  创建特性分支 (`git checkout -b feature/AmazingFeature`)
3.  提交更改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  提交 Pull Request
