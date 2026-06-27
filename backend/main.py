"""ArchGenMAS — 多智能体架构自动生成系统 主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS, RESULT_DIR
from routers import upload, pipeline, result, export, history

app = FastAPI(
    title="ArchGenMAS",
    description="Architecture Generation Multi-Agent System — 多智能体软件架构自动生成系统",
    version="1.0.0",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix="/api", tags=["文件上传"])
app.include_router(pipeline.router, prefix="/api", tags=["流水线执行"])
app.include_router(result.router, prefix="/api", tags=["结果查询"])
app.include_router(export.router, prefix="/api", tags=["文档导出"])
app.include_router(history.router, prefix="/api", tags=["历史记录"])

# 静态文件（生成的PDF等）
RESULT_DIR.mkdir(exist_ok=True)
app.mount("/api/static", StaticFiles(directory=str(RESULT_DIR)), name="static")


@app.get("/")
async def root():
    return {
        "name": "ArchGenMAS",
        "version": "1.0.0",
        "description": "多智能体软件架构自动生成系统",
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
