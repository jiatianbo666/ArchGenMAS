"""PDF 导出服务 — 基于 ReportLab 生成中文 PDF 架构文档"""
import io
import re
from typing import Union
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# 尝试注册中文字体（系统自带或可下载）
_FONT_REGISTERED = False

def _register_fonts():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    # 尝试多个常见中文字体路径
    font_paths = [
        # Windows
        "C:/Windows/Fonts/simsun.ttc",      # 宋体
        "C:/Windows/Fonts/simhei.ttf",      # 黑体
        "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
        "C:/Windows/Fonts/STSONG.TTF",      # 华文宋体
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", fp))
                pdfmetrics.registerFont(TTFont("ChineseFontBold", fp))  # 可能非粗体，但凑合用
                _FONT_REGISTERED = True
                return
            except Exception:
                continue
    # 都没找到，用默认字体（中文会乱码）
    print("WARNING: 未找到中文字体文件，PDF中文可能无法正确显示")


_register_fonts()

FONT_NAME = "ChineseFont" if _FONT_REGISTERED else "Helvetica"
FONT_BOLD = "ChineseFontBold" if _FONT_REGISTERED else "Helvetica-Bold"


def _build_styles():
    """构建段落样式"""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CNTitle", fontName=FONT_BOLD, fontSize=22,
        alignment=TA_CENTER, spaceAfter=12 * mm, leading=30,
    ))
    styles.add(ParagraphStyle(
        name="CNH1", fontName=FONT_BOLD, fontSize=16,
        spaceBefore=10 * mm, spaceAfter=5 * mm, leading=24,
    ))
    styles.add(ParagraphStyle(
        name="CNH2", fontName=FONT_BOLD, fontSize=13,
        spaceBefore=6 * mm, spaceAfter=3 * mm, leading=20,
    ))
    styles.add(ParagraphStyle(
        name="CNBody", fontName=FONT_NAME, fontSize=10,
        alignment=TA_JUSTIFY, spaceAfter=3 * mm, leading=16,
        firstLineIndent=2 * 10 * mm,  # 首行缩进2个中文字符（约20pt）
    ))
    styles.add(ParagraphStyle(
        name="CNCode", fontName="Courier", fontSize=8,
        backColor=HexColor("#f5f5f5"), borderPadding=5,
        spaceAfter=3 * mm, leading=10,
    ))
    styles.add(ParagraphStyle(
        name="CNInfo", fontName=FONT_NAME, fontSize=9,
        textColor=HexColor("#666666"), alignment=TA_CENTER,
    ))
    return styles


def _escape_md(text: str) -> str:
    """简单处理Markdown文本，转为适合ReportLab的格式"""
    # 处理表格 - 转为用 | 分隔的文本
    # 处理PlantUML代码块 - 保留
    lines = text.split("\n")
    result = []
    in_code = False
    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            result.append(f"<pre>{line}</pre>")
        else:
            # 简单Markdown标签转换
            line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
            line = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", line)
            result.append(line)
    return "<br/>".join(result)


async def generate_pdf(markdown_content: str, output_path: Union[str, Path]) -> str:
    """从Markdown生成PDF，返回输出文件路径"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = _build_styles()
    story = []

    # 解析Markdown各部分
    sections = markdown_content.split("\n## ")
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        lines = section.strip().split("\n")

        if i == 0:
            # 标题部分
            title = lines[0].replace("# ", "").strip()
            story.append(Paragraph(title, styles["CNTitle"]))
            story.append(Spacer(1, 5 * mm))
            # 元数据行
            for line in lines[1:]:
                if line.startswith("> "):
                    story.append(Paragraph(line[2:], styles["CNInfo"]))
            story.append(Spacer(1, 10 * mm))
        else:
            heading = lines[0].strip()
            if heading.startswith("# "):
                story.append(Paragraph(heading[2:], styles["CNH1"]))
            else:
                story.append(Paragraph(heading, styles["CNH2"]))
            story.append(Spacer(1, 2 * mm))

            body_text = "\n".join(lines[1:])
            # 处理子标题
            for sub in body_text.split("\n### "):
                if not sub.strip():
                    continue
                sub_lines = sub.strip().split("\n", 1)
                if len(sub_lines) > 1:
                    sub_heading = sub_lines[0].strip()
                    sub_body = sub_lines[1] if len(sub_lines) > 1 else ""
                    story.append(Paragraph(sub_heading, styles["CNH2"]))
                    if sub_body.strip():
                        story.append(Paragraph(_escape_md(sub_body), styles["CNBody"]))
                else:
                    story.append(Paragraph(_escape_md(sub), styles["CNBody"]))

        story.append(Spacer(1, 3 * mm))

    # 构建PDF
    doc.build(story)
    return str(output_path)
