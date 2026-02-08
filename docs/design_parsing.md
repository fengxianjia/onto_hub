# Ontology Parsing & Visualization Design

## 1. 概述 (Overview)
本功能旨在提供“所见即所得”的本体可视化能力。通过可配置的**解析模板 (Parsing Template)**，系统能够自动从 Markdown 文档中提取实体 (Entities) 和关系 (Relationships)，并以图谱形式展示。

## 2. 核心概念 (Core Concepts)

### 2.1 解析模板 (Parsing Template)
定义了如何从非结构化/半结构化的 Markdown 文件中提取结构化数据的规则集合。
*   **适用范围**: 一个模板通常对应一种文档编写规范（如 "Standard Wiki Format", "ADR Format"）。
*   **规则类型**:
    *   **Entity Rules**: 定义如何识别实体（例如：每个文件是一个实体，或者 H1 标题也是实体）。
    *   **Relation Rules**: Define how to identify relationships (e.g., WikiLinks `[[Target]]`, standard links `[Label](Target)`, or Frontmatter lists).

### 2.2 实体 (Entity)
本体中的节点。
*   **属性**: `name`, `type` (class/instance), `metadata` (JSON), `content_preview`.
*   **来源**: 关联到具体的文件和行号。

### 2.3 关系 (Relation)
本体中的边。
*   **属性**: `source`, `target`, `relation_type` (e.g., `is_a`, `related_to`, `depends_on`).

## 3. 数据模型 (Data Model)

### 3.1 ParsingTemplate
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Template ID |
| `name` | String | Template Name |
| `description` | String | Description |
| `rules` | JSON | Configuration for parsing (see below) |
| `created_at` | DateTime | |

### 3.2 OntologyEntity
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Entity ID |
| `package_id` | UUID | Belongs to which ontology package version |
| `name` | String | Entity Name (Unique within package?) |
| `category` | String | e.g., "Concept", "Process", "System" |
| `metadata` | JSON | Extracted attributes |
| `file_path` | String | Source file path |

### 3.3 OntologyRelation
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Relation ID |
| `package_id` | UUID | Belongs to which ontology package version |
| `source_id` | UUID | Source Entity ID |
| `target_id` | UUID | Target Entity ID |
| `relation_type`| String | e.g., "contains", "calls" |

## 4. 解析规则配置 (Rules Configuration)

示例 `rules` JSON 结构:

```json
{
  "entity": {
    "strategy": "file_as_entity", // or "header_as_entity"
    "name_source": "filename_no_ext", // or "frontmatter:title", "h1"
    "category_source": "directory", // or "frontmatter:type", "fixed:Concept"
    "metadata_extraction": [
        { "key": "author", "source": "frontmatter:author" },
        { "key": "status", "source": "frontmatter:status" }
    ]
  },
  "relation": {
    "strategies": [
      {
        "type": "wikilink", // [[Target]] or [[Target|Label]]
        "default_relation": "related_to"
      },
      {
        "type": "frontmatter_list",
        "key": "dependencies",
        "relation": "depends_on"
      }
    ]
  }
}
```

## 5. 业务流程 (Workflow)

1.  **模板管理**: 管理员预先创建/配置 `ParsingTemplate`。
2.  **上传/解析**:
    *   用户上传本体 (或添加版本) 时，**必须**选择一个 `ParsingTemplate` (或使用 Default)。
    *   后端保存文件后，触发异步任务 `ParseOntologyTask`。
    *   任务遍历所有 MD 文件，根据规则提取 Entity 和 Relation，批量写入数据库。
3.  **可视化**:
    *   前端调用 `GET /api/ontologies/{id}/graph`。
    *   后端返回 Node/Link 数据格式 (适配 D3.js / ECharts / AntV G6)。
    *   前端渲染 Force Directed Graph。

## 6. API 设计

*   `GET /api/templates`: List templates
*   `POST /api/templates`: Create template
*   `POST /api/ontologies/{id}/parse`: Trigger parsing (Manual retry)
*   `GET /api/ontologies/{id}/graph`: Get graph data
    *   Response: `{ "nodes": [...], "edges": [...] }`

## 7. 前端设计
*   **Template Manager**: simple CRUD table with JSON editor for rules.
*   **Upload Dialog**: Add "Parsing Template" dropdown.
*   **Ontology Detail**: Add "Knowledge Graph" (知识图谱) tab.
    *   Left: Canvas (Force Graph).
    *   Right: Node Detail Panel (click node to show metadata & source file link).
