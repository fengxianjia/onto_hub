import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("api.request")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    API 请求审计与性能日志中间件
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # 排除静态资源和健康检查
        if request.url.path.startswith(("/assets", "/docs", "/openapi.json")):
            return await call_next(request)

        start_time = time.time()
        
        # 记录请求基本信息
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000  # ms
            
            # 记录响应信息
            logger.info(
                f"{client_ip} - \"{method} {request.url.path}\" {response.status_code} - "
                f"Spent: {process_time:.2f}ms"
            )
            
            # 添加处理时间 Header (可选)
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"{client_ip} - \"{method} {request.url.path}\" FAILED - "
                f"Error: {str(e)} - Spent: {process_time:.2f}ms",
                exc_info=True
            )
            raise
