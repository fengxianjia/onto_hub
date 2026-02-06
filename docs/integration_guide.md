# SDK 与订阅集成指南

本模块提供了 Python SDK (`backend.app.sdk`)，允许项目内其他模块直接调用本体管理功能，而无需通过 HTTP API。

## 1. 导入 SDK

```python
# 确保 backend 目录在 PYTHONPATH 中
import sys
import os
sys.path.append("/path/to/onto_manage/backend")

from app.sdk import OntologySDK
```

## 2. 使用 SDK 读取数据

### 获取列表

```python
packages = OntologySDK.get_ontologies()
for pkg in packages:
    print(pkg.name, pkg.id)
```

### 读取 MD 文件内容

```python
content = OntologySDK.get_file_content(
    package_id="your-uuid-here",
    file_path="concepts/user.md"
)
print(content)
```

## 3. 事件订阅 (Subscription)

您可以订阅本体上传完成后的事件，用于触发自动化任务（如知识图谱解析、索引构建）。

### 支持的事件

*   `ontology.uploaded`: 当 ZIP 包上传解压完成并存入数据库后触发。

### 使用示例

建议在应用启动时（或在其他服务的初始化代码中）注册监听器。

```python
from app.sdk import OntologySDK

def on_ontology_uploaded(payload):
    print("收到新本体上传通知！")
    print(f"ID: {payload['package_id']}")
    print(f"文件名: {payload['name']}")
    print(f"文件数量: {payload['file_count']}")
    
    # 在这里执行你的后续逻辑，例如：
    # task_queue.push(payload['package_id'])

# 注册回调
OntologySDK.subscribe("ontology.uploaded", on_ontology_uploaded)
```

## 架构说明

*   **SDK** 本质上是 `OntologyManager` 和 `Database Session` 的一层封装。
*   **事件机制** 目前基于进程内内存 (In-Memory)，仅适用于单进程运行。如果在多进程 (Gunicorn Workers) 环境下，只有与上传请求在同一进程的 Subscriber 会收到通知。

---

# 远程集成 (Docker/Microservices)

如果您的项目运行在独立的 Docker 容器或服务器上，**不能**直接使用 `OntologySDK` (因为它依赖本地数据库文件和磁盘)。

请使用我们提供的 **HTTP Client** (`backend/client.py`)。

## 1. 复制 Client 代码

将 `backend/client.py` 文件复制到您的项目中。

## 2. 使用示例

```python
from client import OntologyClient

# 初始化 Client，指向本体管理服务的地址
client = OntologyClient("http://ontology-service:8000")

# 1. 上传
result = client.upload_ontology("./my_ontology.zip")
print(f"Uploaded ID: {result['id']}")

# 2. 读取文件
content = client.get_file_content(result['id'], "summary.md")
print(content)
```

## 3. 关于事件订阅 (Webhooks)

对于远程集成，我们推荐使用 **Webhook** 机制。您可以注册一个 HTTP URL，当本体上传完成时，系统会向该 URL 发送 POST 请求。

### 注册 Webhook

```python
# 注册接收地址
webhook = client.subscribe_webhook("http://your-service:8080/callbacks/ontology")
print(f"Webhook ID: {webhook['id']}")
```

### 接收通知 (Webhook Handler)

现在的 Webhook 请求采用 `multipart/form-data` 格式，包含 JSON 数据和 ZIP 文件。

您需要在您的服务中提供一个 HTTP 接口（例如使用 Flask/FastAPI）：

```python
from fastapi import FastAPI, Request, Form, File, UploadFile
import json

app = FastAPI()

@app.post("/callbacks/ontology")
async def on_ontology_event(
    payload: str = Form(...),    # JSON 字符串
    file: UploadFile = File(...) # 原始 ZIP 文件
):
    data = json.loads(payload)
    print(f"收到事件: {data['event']}")
    print(f"新本体ID: {data['package_id']}")
    
    # 保存或处理 ZIP 文件
    content = await file.read()
    with open(f"received_{data['package_id']}.zip", "wb") as f:
        f.write(content)
        
    # 触发您的后续处理逻辑...
    return {"status": "ok"}
```

## 4. 动态订阅管理最佳实践 (Dynamic Management)

为了确保您的服务始终能接收到通知，且不产生重复订阅，建议遵循 **"启动时注册 (On-Startup Registration)"** 模式。

### 自动化注册示例

在您的服务启动代码中（例如 `main.py` 或 `app_start` 事件）：

```python
def ensure_subscriptions(client, callback_url):
    """确保 Webhook 已注册 (后端已实现幂等性，重复调用安全)"""
    try:
        # 尝试注册 (如果已存在，会返回旧的 ID)
        webhook = client.subscribe_webhook(callback_url)
        print(f"Webhook 订阅活跃: ID={webhook['id']}")
    except Exception as e:
        print(f"Webhook 注册失败: {e}")

# 服务启动时调用
my_callback_url = "http://my-service:8080/callbacks/ontology"
ensure_subscriptions(ontology_client, my_callback_url)
```

### 管理接口

我们提供了完整的 API 用于动态管理：

1.  **查看所有订阅**: `client.list_webhooks()`
2.  **取消订阅**: `client.unsubscribe_webhook(webhook_id)`

您可以开发一个简单的管理后台或 CLI 工具来调用这些接口，根据需要开启或关闭特定服务的通知。
