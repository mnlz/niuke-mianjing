from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from niuke_mianjing_backend.api.deps import get_schedule_service, get_wechat_service
from niuke_mianjing_backend.api.middleware.auth import AuthMiddleware
from niuke_mianjing_backend.api.middleware.error_handler import AppException, app_exception_handler, generic_exception_handler
from niuke_mianjing_backend.api.routes import crawl, logs, schedule, wechat, ws
from niuke_mianjing_backend.repositories.database import DatabasePool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await DatabasePool.init()
    print("数据库连接池初始化完成")

    schedule_service = get_schedule_service()
    await schedule_service.init_table()
    print("定时任务表初始化完成")

    wechat_service = get_wechat_service()
    await wechat_service.init_table()
    print("微信公众号稿件表初始化完成")

    schedule_service.start()
    print("定时任务调度器已启动")
    print("应用启动成功")

    yield

    schedule_service.stop()
    print("定时任务调度器已停止")

    await DatabasePool.close()
    print("数据库连接池已关闭")
    print("应用关闭")


app = FastAPI(
    title="牛客面经爬虫 API",
    description="""
## 牛客面经爬虫系统 API

支持快速爬取、定时任务、日志查询、Markdown 导出、卡片生成、微信公众号草稿生成和 WebSocket 实时推送。
""",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/", tags=["系统"])
async def root():
    return {"message": "牛客面经爬虫 API", "version": "2.0.0", "docs": "/docs"}


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "healthy"}


app.include_router(schedule.router)
app.include_router(logs.router)
app.include_router(ws.router)
app.include_router(crawl.router)
app.include_router(wechat.router)
