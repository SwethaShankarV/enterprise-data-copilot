# app/agents/orchestrator.py
import logging
import re
from app.agents.analyst_agent import AnalystAgent
from app.agents.insight_agent import InsightAgent

logger = logging.getLogger(__name__)

FOLLOWUP_KEYWORDS = [
    "break", "drill", "drilldown", "drill-down", "show", "list", "detail",
    "details", "filter", "compare", "top", "bottom", "group", "by", "split",
    "segment", "breakdown", "explain"
]

DATA_KEYWORDS = ["revenue", "sales", "region", "product", "order", "orders", "avg", "quantity", "count"]

# Short courtesy / closing phrases that should get a friendly reply, not the data-only fallback
COURTESY_PHRASES = [
    "thanks", "thank you", "thx", "ty", "ok", "okay", "got it", "perfect",
    "great", "cool", "awesome", "bye", "goodbye", "done", "that's all"
]

def is_courtesy_message(text: str) -> bool:
    """True if the message is a short courtesy/closing phrase."""
    t = (text or "").strip().lower()
    if not t or len(t) > 50:
        return False
    # Remove punctuation for matching
    t_clean = re.sub(r"[^\w\s]", "", t)
    words = set(t_clean.split())
    return any(phrase.replace(" ", "") in t_clean.replace(" ", "") or phrase in words for phrase in COURTESY_PHRASES)

def _message_content(m) -> str:
    """Get content from either a dict message or an OpenAI ChatCompletionMessage."""
    if hasattr(m, "content"):
        return (m.content or "") or ""
    if isinstance(m, dict):
        return m.get("content", "") or ""
    return ""

# small helper to detect if message is short / follow-up style
def is_short_followup(text: str, char_threshold: int = 40, token_threshold: int = 8) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if len(t) <= 3:  # e.g., "Yes", "No"
        return False
    # If it begins with a verb-like word (break/show/drill) — strong signal
    if re.match(r"^(break|show|drill|list|filter|compare|explain|expand)\b", t.lower()):
        return True
    # short overall message is likely a follow-up (e.g., "Break that down")
    words = t.split()
    if len(t) < char_threshold or len(words) <= token_threshold:
        # also check if it contains a followup keyword somewhere ("break", "drill", etc.)
        if any(k in t.lower() for k in FOLLOWUP_KEYWORDS):
            return True
    return False

def last_turn_mentioned_data(messages) -> bool:
    """
    Inspect conversation history to see if previous turns referenced data-related intent
    or produced numeric/aggregate results. This helps decide if a followup without keywords
    should still be routed to AnalystAgent.
    """
    if not messages or len(messages) < 2:
        return False

    # search last few turns (user + assistant) for data keywords or numeric outputs
    window = messages[-6:]  # check up to last 6 messages for context
    # text = " ".join([m.get("content","") for m in window]).lower()
    text = " ".join([_message_content(m) for m in window]).lower()

    # 1) explicit data keywords
    if any(k in text for k in DATA_KEYWORDS):
        return True

    # 2) assistant produced numeric results or table-like output (presence of currency, numbers, or "breakdown")
    # crude heuristics: $, % or sequences of digits with commas, or "breakdown" / "by product"
    if re.search(r"\$\d+|%|\d{1,3}(,\d{3})+|\b\d+\b", text):
        return True

    if "breakdown" in text or "by product" in text or "by region" in text:
        return True

    return False

class Orchestrator:
    def __init__(self):
        self.analyst = AnalystAgent()
        self.insight = InsightAgent()

    def route(self, messages):
        """
        Routing logic:
        1. If user message includes strong data keywords, call AnalystAgent.
        2. Else if message looks like a short follow-up AND the session context indicates recent data,
           route to AnalystAgent (to handle follow-ups like "Break that down").
        3. Else handle as non-data / fallback.
        """

        # Assume messages is a list of dicts and the last entry is the latest user message
        if not messages:
            return "I don't have any message context.", None

        last_msg = messages[-1]["content"].strip().lower()
        logger.info(
            "Orchestrator: last_msg=%s short_followup=%s recent_data=%s",
            last_msg,
            is_short_followup(last_msg),
            last_turn_mentioned_data(messages[:-1]),
        )

        # 1) direct keyword match
        if any(word in last_msg for word in DATA_KEYWORDS):
            analysis_text, structured = self.analyst.handle(messages)
            if structured:
                summary = self.insight.summarize(structured)
                return summary, structured
            return analysis_text, None

        # 2) follow-up heuristic: short & has followup-type verb OR session context indicates recent data
        if is_short_followup(last_msg) and last_turn_mentioned_data(messages[:-1]):
            # treat as follow-up and route to analyst
            analysis_text, structured = self.analyst.handle(messages)
            if structured:
                summary = self.insight.summarize(structured)
                return summary, structured
            return analysis_text, None

        # 3) If message is short but doesn't match follow-up heuristics, still check for subtle followup forms:
        #    e.g., "What about the East?" -> contains "what about" which suggests follow-up
        if re.match(r"^(what about|and|also|how about)\b", last_msg):
            if last_turn_mentioned_data(messages[:-1]):
                analysis_text, structured = self.analyst.handle(messages)
                if structured:
                    summary = self.insight.summarize(structured)
                    return summary, structured
                return analysis_text, None

        # 4) Courtesy / closing phrases → friendly acknowledgment, do not route to Analyst
        if is_courtesy_message(last_msg):
            return "You're welcome! Ask anytime if you need more data or another breakdown.", None

        # 5) fallback for actual out-of-scope data requests
        return "I can only answer questions about the enterprise sales data. The data is in the \"sales\" table (revenue, region, product, orders). Please rephrase if you want data analysis.", None