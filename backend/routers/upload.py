"""文件上传接口"""
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from config import UPLOAD_DIR
from services.file_parser import parse_file, extract_preview

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传需求文档（支持 .txt / .docx / .md）"""
    # 检查文件格式
    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    if suffix not in (".txt", ".docx", ".md"):
        raise HTTPException(400, f"不支持的文件格式: {suffix}，仅支持 .txt / .docx / .md")

    # 保存文件
    file_id = uuid.uuid4().hex[:12]
    save_path = UPLOAD_DIR / f"{file_id}{suffix}"
    content_bytes = await file.read()

    if len(content_bytes) == 0:
        raise HTTPException(400, "文件内容为空")

    save_path.write_bytes(content_bytes)

    # 解析文件
    try:
        content, filename = await parse_file(save_path)
    except Exception as e:
        raise HTTPException(500, f"文件解析失败: {str(e)}")

    if not content.strip():
        raise HTTPException(400, "文件解析后无有效内容")

    return JSONResponse({
        "file_id": file_id,
        "filename": filename,
        "content_preview": extract_preview(content),
        "content_full": content,
        "char_count": len(content),
        "status": "parsed",
    })
