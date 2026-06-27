"""流水线执行接口 + WebSocket 进度推送"""
import asyncio
import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from orchestrator.mediator import mediator

router = APIRouter()


class PipelineRunRequest(BaseModel):
    content: str
    filename: str = ""
    architecture_style: str = "auto"
    max_iterations: int = 3


class PipelineRunResponse(BaseModel):
    project_id: str
    status: str


@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(req: PipelineRunRequest):
    """启动流水线（异步后台执行）"""
    if not req.content.strip():
        raise HTTPException(400, "需求内容不能为空")

    # 创建项目
    project_id = mediator.create_project(
        raw_document=req.content,
        filename=req.filename,
        style_preference=req.architecture_style,
        max_iterations=req.max_iterations,
    )

    # 后台执行流水线
    asyncio.create_task(mediator.run_pipeline(project_id))

    return PipelineRunResponse(project_id=project_id, status="started")


@router.get("/pipeline/{project_id}/status")
async def get_pipeline_status(project_id: str):
    """查询流水线执行状态"""
    blackboard = mediator.get_blackboard(project_id)
    if not blackboard:
        raise HTTPException(404, "项目不存在")

    return {
        "project_id": blackboard.project_id,
        "stage": blackboard.pipeline_stage,
        "agent_statuses": {k: v.value for k, v in blackboard.agent_statuses.items()},
        "iteration": blackboard.iteration,
        "max_iterations": blackboard.max_iterations,
        "logs": blackboard.logs[-50:],  # 最近50条
        "created_at": blackboard.created_at,
        "updated_at": blackboard.updated_at,
    }


@router.websocket("/ws/pipeline/{project_id}")
async def websocket_pipeline(websocket: WebSocket, project_id: str):
    """WebSocket 实时推送流水线进度"""
    await websocket.accept()

    blackboard = mediator.get_blackboard(project_id)
    if not blackboard:
        await websocket.send_json({"type": "error", "message": "项目不存在"})
        await websocket.close()
        return

    async def push_status(data: dict):
        """回调：将黑板状态推送到 WebSocket"""
        try:
            await websocket.send_json({
                "type": "status_update",
                **data,
            })
        except Exception:
            pass

    mediator.register_callback(project_id, push_status)

    try:
        # 发送初始状态
        await websocket.send_json({
            "type": "connected",
            "project_id": project_id,
            "stage": blackboard.pipeline_stage,
        })

        # 保持连接，等待流水线完成
        while True:
            await asyncio.sleep(1)
            blackboard = mediator.get_blackboard(project_id)
            if not blackboard:
                break
            if blackboard.pipeline_stage in ("done", "error"):
                await websocket.send_json({
                    "type": "pipeline_complete",
                    "project_id": project_id,
                    "stage": blackboard.pipeline_stage,
                })
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
