"""全局配置模块 — 从 .env 文件加载配置"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（优先级：同目录 .env > 父目录 .env）
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    # 尝试从项目根目录加载
    ROOT_ENV = BASE_DIR.parent / ".env"
    if ROOT_ENV.exists():
        load_dotenv(ROOT_ENV)

# LLM 配置（SiliconFlow — OpenAI 兼容接口）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3.5-35B-A3B")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# 不同 Agent 可选用不同模型（不设置则默认用 LLM_MODEL）
AGENT_MODELS = {
    "requirement": os.getenv("REQUIREMENT_MODEL", LLM_MODEL),
    "architecture": os.getenv("ARCHITECTURE_MODEL", LLM_MODEL),
    "review": os.getenv("REVIEW_MODEL", LLM_MODEL),
    "risk": os.getenv("RISK_MODEL", LLM_MODEL),
    "document": os.getenv("DOCUMENT_MODEL", LLM_MODEL),
}

# 启动时检查 API Key
if not LLM_API_KEY or LLM_API_KEY.startswith("sk-your"):
    import sys
    sys.stderr.write(f"[WARNING] LLM_API_KEY not configured or using default value!\n")
    sys.stderr.write(f"[WARNING] Please set your real API key in: {ENV_FILE}\n")

# 迭代控制
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))

# 文件存储
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"
UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
