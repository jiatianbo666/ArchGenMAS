"""历史记录 API"""
from fastapi import APIRouter, HTTPException, Query
from services.history_db import list_projects, count_projects, get_project, delete_project

router = APIRouter()


@router.get("/history")
async def get_history(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    """分页获取历史记录"""
    items = await list_projects(page=page, size=size)
    total = await count_projects()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get("/history/{project_id}")
async def get_history_item(project_id: str):
    """获取单个历史项目详情"""
    item = await get_project(project_id)
    if not item:
        raise HTTPException(404, "项目不存在")
    return item


@router.delete("/history/{project_id}")
async def delete_history_item(project_id: str):
    """删除历史记录"""
    ok = await delete_project(project_id)
    if not ok:
        raise HTTPException(404, "项目不存在")
    return {"status": "deleted", "project_id": project_id}
