"""LLM 客户端封装 — OpenAI 兼容接口（适配 SiliconFlow / 推理模型）"""
import json
import re
import asyncio
from typing import Optional
import httpx
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE


class LLMClient:
    """统一的 LLM 调用客户端，支持 OpenAI 兼容接口"""

    def __init__(
        self,
        api_key: str = LLM_API_KEY,
        base_url: str = LLM_BASE_URL,
        model: str = LLM_MODEL,
        max_tokens: int = LLM_MAX_TOKENS,
        temperature: float = LLM_TEMPERATURE,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def _extract_content(self, data: dict) -> str:
        """从 API 响应中提取内容，兼容推理模型的 reasoning_content"""
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})

        # 优先取 content
        content = msg.get("content", "")
        if content and content.strip():
            return content.strip()

        # Qwen/DeepSeek 推理模型：content 为空时回退到 reasoning_content
        reasoning = msg.get("reasoning_content", "")
        if reasoning and reasoning.strip():
            # reasoning_content 通常以 "Thinking Process:" 开头
            # 尝试从中提取 JSON（Qwen 推理模型有时把结果写在思考末尾）
            # 先尝试找到最后的 {} JSON 块
            json_match = re.search(r"\{[\s\S]*\}", reasoning)
            if json_match:
                return json_match.group()

            # 找不到 JSON 就返回 reasoning 尾部（去掉 "Thinking Process" 前缀）
            lines = reasoning.strip().split("\n")
            # 取最后几段作为实际输出
            return "\n".join(lines[-30:])

        # 全空
        return ""

    async def chat(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """发送对话请求，返回文本响应"""
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        async with httpx.AsyncClient(timeout=180.0) as client:
            last_error = None
            for attempt in range(3):
                try:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                    )
                    if resp.status_code >= 400:
                        try:
                            err_data = resp.json()
                            err_msg = err_data.get("error", {}).get("message", resp.text)
                        except Exception:
                            err_msg = resp.text
                        raise RuntimeError(f"API error [{resp.status_code}]: {str(err_msg)[:500]}")

                    data = resp.json()
                    content = self._extract_content(data)

                    if not content:
                        # 最后一次尝试：打印完整响应帮助调试
                        raise RuntimeError(
                            f"LLM returned empty content. "
                            f"finish_reason={data.get('choices',[{}])[0].get('finish_reason')}. "
                            f"Raw: {json.dumps(data, ensure_ascii=False)[:800]}"
                        )

                    return content

                except RuntimeError:
                    raise
                except Exception as e:
                    last_error = e
                    if attempt == 2:
                        raise RuntimeError(f"LLM call failed (3 retries): {str(last_error)[:500]}")
                    await asyncio.sleep(1.0 * (attempt + 1))

        raise RuntimeError(f"LLM call failed: {str(last_error)[:500]}")

    async def chat_json(self, system_prompt: str, user_prompt: str, **kwargs) -> dict:
        """发送对话请求，自动提取 JSON 响应（增强容错）"""
        text = await self.chat(system_prompt, user_prompt, **kwargs)

        # 策略1: 移除 markdown 代码块标记后提取 JSON
        cleaned = text
        code_block_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if code_block_match:
            cleaned = code_block_match.group(1)

        # 策略2: 提取最外层完整 JSON 对象
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 策略3: 整个 cleaned 文本就是 JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 策略4: 尝试修复常见 JSON 错误（尾逗号等）
        try:
            fixed = re.sub(r",(\s*[}\]])", r"\1", cleaned)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        return {"raw_text": text, "error": f"Cannot parse as JSON. Response preview: {text[:500]}"}


# 全局默认客户端
default_client = LLMClient()


def get_client(model_override: Optional[str] = None) -> LLMClient:
    """获取 LLM 客户端，可选覆盖模型"""
    if model_override:
        return LLMClient(model=model_override)
    return default_client
