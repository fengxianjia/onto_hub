from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query, Request, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List
import os
from datetime import datetime, UTC

from .config import settings
from .core.logging import setup_logging

from .core.errors import BusinessException, BusinessCode, handle_result
from fastapi.responses import JSONResponse

from . import models, schemas, database, utils

# 数据库初始化函数
def init_db():
    models.Base.metadata.create_all(bind=database.engine)

# 在非测试环境下自动初始化
if settings.ENV != "test":
    init_db()
from .repositories.ontology_repo import OntologyRepository
from .repositories.webhook_repo import WebhookRepository
from .services.ontology_service import OntologyService
from .services.webhook_service import WebhookService
from .tasks import parse_ontology_task
from .core.middleware import LoggingMiddleware
from .routers import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    # Initialize logging during application startup
    setup_logging()
    logging.info("FastAPI application is starting up...")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="专业级的本体管理枢纽 - 支持版本控制、异步推送与解耦架构",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

from .routers import templates, ontologies, webhooks

# 注册路由
app.include_router(templates.router)
app.include_router(ontologies.router)
app.include_router(webhooks.router)

# 注册中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.business_code,
            "detail": exc.detail or "Business error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
