"""
Google ADK Title Agent
This agent generates SEO-optimized technical book titles and subtitles.
"""

from typing import List, Dict, Any
from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini

from google.genai import types

RETRY_CONFIG = types.HttpRetryOptions(
    attempts=10,           # Maximum retry attempts
    exp_base=7,           # Exponential backoff base
    initial_delay=2,      # Start with 1s delay
    http_status_codes=[   # Retry on these HTTP status codes
        429,  # Too Many Requests / rate limited / resource exhausted
        500,  # Internal server error
        503,  # Service unavailable
        504,  # Gateway timeout
    ],
)

GEMINI_MODEL = Gemini(
                model="gemini-2.0-flash",
                retry_options=RETRY_CONFIG
                )  # same as other agents

# ---------------------------------------------------------------------------
# TOOL: emit_titles
# ---------------------------------------------------------------------------
def emit_titles(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ADK FunctionTool
    ----------------
    Must use SIMPLE JSON types only.

    Expected input:
    [
        {
            "title": "string",
            "subtitle": "string",
            "seo_keywords": ["kw1", "kw2", "kw3"]
        }
    ]

    ADK automatically validates this because it is just:
        List[Dict[str, Any]]
    """
    return {"titles": candidates}


# ---------------------------------------------------------------------------
# AGENT DEFINITION
# ---------------------------------------------------------------------------

root_agent = Agent(
    model=GEMINI_MODEL,
    name="title_agent",
    description="Generates SEO-optimized, non-copyrighted technical book titles.",
    instruction="""
        You are a professional title generation assistant for technical books.

        When the user provides a topic (e.g., “Modern API Testing with Playwright”):

        1. Think of up to 10 unique, original book titles (max 8 words each).
        2. For each title, generate a one-line subtitle.
        3. Provide exactly 3 short SEO keywords.
        4. NEVER output raw text. ALWAYS call the function tool `emit_titles`.

        Call the tool once using this JSON shape:

        [
        {
            "title": "string",
            "subtitle": "string",
            "seo_keywords": ["kw1","kw2","kw3"]
        }
        ]
        """,
    tools=[emit_titles],
)
