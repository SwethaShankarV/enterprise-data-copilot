import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# ENV-driven config
USE_AZURE = os.getenv("USE_AZURE_OPENAI", "false").lower() in ("1", "true", "yes")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")


def normalize_messages(messages):
    """Convert messages to plain dicts for the API. Preserves tool messages and assistant tool_calls."""
    norm = []
    for m in messages:
        if isinstance(m, dict):
            out = dict(m)
            if "tool_call_id" in out:
                norm.append({"role": out.get("role", "tool"), "tool_call_id": out["tool_call_id"], "content": out.get("content", "")})
            else:
                norm.append({"role": out.get("role", "user"), "content": out.get("content", "")})
            continue
        role = getattr(m, "role", None) or "user"
        content = getattr(m, "content", None) or ""
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls is not None:
            tc_list = []
            for tc in tool_calls:
                tc_id = getattr(tc, "id", None) or (tc.get("id") if isinstance(tc, dict) else None)
                fn = getattr(tc, "function", None) or (tc.get("function") if isinstance(tc, dict) else {})
                fn_name = getattr(fn, "name", None) or (fn.get("name") if isinstance(fn, dict) else "")
                fn_args = getattr(fn, "arguments", None) or (fn.get("arguments") if isinstance(fn, dict) else "{}")
                tc_list.append({"id": tc_id, "type": "function", "function": {"name": fn_name, "arguments": fn_args}})
            norm.append({"role": role, "content": content or None, "tool_calls": tc_list})
        else:
            norm.append({"role": role, "content": content or ""})
    return norm


class LLMClient:
    def __init__(self):
        if USE_AZURE:
            if not AZURE_API_KEY or not AZURE_ENDPOINT or not AZURE_DEPLOYMENT:
                raise ValueError("Azure OpenAI env vars missing (AZURE_OPENAI_KEY / ENDPOINT / DEPLOYMENT)")
            self.client = OpenAI(api_key=AZURE_API_KEY, base_url=AZURE_ENDPOINT.rstrip("/") + "/")
            logger.info("LLMClient: configured for Azure OpenAI (deployment=%s)", AZURE_DEPLOYMENT)
        else:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("LLMClient: configured for OpenAI (model=%s)", MODEL_NAME)

    def chat(self, messages, tools=None, tool_choice="auto"):
        norm = normalize_messages(messages)
        if USE_AZURE:
            kwargs = {"model": AZURE_DEPLOYMENT, "messages": norm}
            if tools is not None:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception:
                logger.exception("Azure LLM call failed")
                raise
        else:
            kwargs = {"model": MODEL_NAME, "messages": norm}
            if tools is not None:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception:
                logger.exception("OpenAI LLM call failed")
                raise
