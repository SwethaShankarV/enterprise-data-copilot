import json
import logging
from app.tools.sql_adapter import run_sql_query
from app.tools.retriever import retrieve_relevant_docs
from app.llm_client import LLMClient

logger = logging.getLogger(__name__)

def _extract_message(response):
    try:
        return response.choices[0].message
    except Exception:
        try:
            return response["choices"][0]["message"]
        except Exception:
            logger.exception("Could not extract message from LLM response")
            return None

class AnalystAgent:
    def __init__(self):
        self.llm = LLMClient()

    def handle(self, messages):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_sql_query",
                    "description": "Run a SQL query on the enterprise sales database. The only table is \"sales\" with columns: id, region, product, revenue, order_date. Use these exact column names (e.g. \"product\", not \"product_line\"). Return the query as the \"query\" parameter.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        # RAG: inject relevant metric definitions into context for the first LLM call
        last_user = messages[-1].get("content", "") if messages else ""
        docs = retrieve_relevant_docs(last_user, top_k=3)
        if docs:
            defs_text = "\n\n".join(d["text"] for d in docs)
            if messages and messages[0].get("role") == "system":
                first = dict(messages[0])
                first["content"] = first["content"] + "\n\nRelevant metric definitions (use when applicable):\n" + defs_text
                messages_for_llm = [first] + list(messages[1:])
            else:
                messages_for_llm = [{"role": "system", "content": "Relevant metric definitions (use when applicable):\n" + defs_text}] + list(messages)
        else:
            messages_for_llm = list(messages)

        try:
            response = self.llm.chat(messages_for_llm, tools=tools)
        except Exception as e:
            logger.exception("LLM chat call failed")
            return f"Error calling LLM: {e}", None

        message = _extract_message(response)
        if message is None:
            return "Unexpected LLM response shape", None

        # Robust access to tool_calls (SDK object or dict-like)
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls is None and isinstance(message, dict):
            tool_calls = message.get("tool_calls")

        if tool_calls:
            messages.append(message)
            result = None
            for tc in tool_calls:
                tc_id = getattr(tc, "id", None) or (tc.get("id") if isinstance(tc, dict) else None)
                fn = getattr(tc, "function", None) or (tc.get("function") if isinstance(tc, dict) else None)
                if fn is None:
                    continue
                args_str = getattr(fn, "arguments", None) or (fn.get("arguments") if isinstance(fn, dict) else "")
                try:
                    arguments = json.loads(args_str) if args_str else {}
                except json.JSONDecodeError:
                    logger.warning("Invalid tool call arguments: %s", args_str)
                    continue
                result = run_sql_query(arguments.get("query", ""))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": json.dumps(result)
                })
            try:
                second = self.llm.chat(messages)
            except Exception as e:
                logger.exception("LLM second chat call failed")
                return f"Error calling LLM: {e}", result
            final_msg = _extract_message(second)
            final_text = (
                getattr(final_msg, "content", None) or (final_msg.get("content") if isinstance(final_msg, dict) else "")
            ) or ""
            return final_text, result

        content = getattr(message, "content", None) or (message.get("content") if isinstance(message, dict) else "")
        return content or "", None