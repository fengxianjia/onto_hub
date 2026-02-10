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

### 3. 安全与纵深防御 (Security & Deep Defense)
*   **ZIP 攻击防护**：
    *   **Zip Slip 防御**：重构路径校验算法，严禁非法路径逃逸。
    *   **ZIP 炸弹防御**：实时解压限额统计，严格限制总容量 (500MB) 与文件数 (1000个)。
*   **正则 ReDoS 加固**：解析引擎内置超时与异常处理，防止恶意构造的正则导致 CPU 耗尽。
*   **删除保护**：Active 版本及下游耦合版本（通过 Webhook 追踪）严禁物理删除。

### 4. 插件式解析引擎 (Plugin-based Parsing)
*   **解耦架构**：核心引擎与具体格式解析解耦，支持热插拔。
*   **多格式支持**：默认支持 Markdown (含 Frontmatter/表格)，并预留了 OWL、JSON 接入口。
*   **自动发现**：基于 `pkgutil` 实现插件自动扫描与注册机制。

---
### 5. 可视化与探索 (Visualization)
*   **多维视图**：提供文件树、知识图谱及本地时间显示的实体/关系列表。
*   **组件化重构**：前端完全基于 Vue 组件化架构，逻辑清晰，性能优异。

---

## 技术栈 (Tech Stack)

*   **后端 (Backend)**: Python 3.10+, **FastAPI**, **SQLAlchemy**, **Pytest** (集成测试)
*   **前端 (Frontend)**: **Vue 3**, **Vite**, **Element Plus**, **LocalTimeZone-aware**

---

## 快速开始 (Quick Start)

### 1. 环境准备
确保您的环境已安装：Python 3.10+, Node.js 18+, Git

### 2. 启动与测试
```bash
# 后端启动
python run.py

# 运行全量安全与集成测试
cd backend
./test.ps1

# 前端开发模式
cd frontend && npm install && npm run dev
```

---

## 目录结构 (Project Structure)

```text
onto_hub/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── parsers/    # [NEW] 插件解析器目录 (Markdown, Base...)
│   │   │   └── ...
│   │   ├── repositories/   # 数据访问层
│   │   ├── routers/        # API 路由
│   │   └── models.py       # 数据模型
│   ├── tests/              # [UPDATED] 全量集成测试 (Security, Parsing)
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/     # [REFACTORED] 已拆分的原子化组件
│   │   ├── utils/          # [NEW] 格式化工具 (format.js)
│   │   └── ...
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
