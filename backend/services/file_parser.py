"""文件解析服务 — 支持 TXT 和 DOCX"""
from pathlib import Path
from typing import Tuple, Union


async def parse_file(file_path: Union[str, Path]) -> Tuple[str, str]:
    """解析文件，返回 (文本内容, 文件名)"""
    path = Path(file_path)
    filename = path.name
    suffix = path.suffix.lower()

    if suffix == ".txt":
        content = path.read_text(encoding="utf-8")
        return content, filename

    elif suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)
            return content, filename
        except ImportError:
            raise RuntimeError("python-docx 未安装，无法解析 .docx 文件")

    elif suffix == ".md":
        content = path.read_text(encoding="utf-8")
        return content, filename

    else:
        raise ValueError(f"不支持的文件格式: {suffix}，仅支持 .txt / .docx / .md")


def extract_preview(content: str, max_chars: int = 500) -> str:
    """提取文本预览（前N字）"""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "..."
