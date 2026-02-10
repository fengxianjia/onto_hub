import uvicorn
import os
import sys

# 将 backend 目录添加到 Python 路径，以便能找到 app 包
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

if __name__ == "__main__":
    # 使用 reload=True 在开发模式下运行
    # app 导入路径变为 app.main:app
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=False)
