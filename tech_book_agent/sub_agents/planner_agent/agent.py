"""
Google ADK Planner Agent

This agent generates a complete 11-chapter outline (plan) for a technical book,
based on:
- Selected title
- Subtitle
- Topic / idea
- Target audience

The plan is emitted as structured JSON via a single function tool `emit_plan`.
"""

from typing import Dict, Any
from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from typing import Dict, Any
from pathlib import Path
import json
import re

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

# ---------------------------------------------------------------------------
# TOOL: persist_plan
# ---------------------------------------------------------------------------
def persist_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    ADK FunctionTool

    In addition to returning the `plan` to the agent, this function
    PERSISTS the plan as JSON on disk so that other agents (writer, docx,
    supervisor) can reuse it later.

    Behavior:
    - Determine a safe folder name from plan["title"].
    - Create a directory at: <PROJECT_ROOT>/<slug_title>/
    - Write the plan to: <book_dir>/plan.json
    - Attach a `storage` section to the plan with paths.

    The return value is the same plan object, enriched with storage info:
    {
      ...original plan fields...,
      "storage": {
        "book_dir": "...absolute path...",
        "plan_path": "...absolute path..."
      }
    }
    """
    try:
        title = plan.get("title") or "untitled-book"
    except AttributeError:
        # If plan wasn't even a dict, just wrap it and bail out
        title = "untitled-book"
        plan = {"title": title, "plan": plan}

    slug = _slugify(title)
    book_dir = PROJECT_ROOT / slug
    book_dir.mkdir(parents=True, exist_ok=True)

    plan_path = book_dir / "plan.json"

    try:
        with plan_path.open("w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        storage_info = {
            "book_dir": str(book_dir),
            "plan_path": str(plan_path),
        }
    except Exception as exc:
        # If writing fails, at least return the error info so the supervisor
        # can decide what to do.
        storage_info = {
            "error": f"Failed to persist plan: {exc!r}",
        }

    # Attach storage metadata for downstream agents
    if isinstance(plan, dict):
        plan.setdefault("storage", {})
        plan["storage"].update(storage_info)
    else:
        plan = {
            "title": title,
            "data": plan,
            "storage": storage_info,
        }

    return plan

# Detect project root (tech-book-agent directory)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _slugify(name: str) -> str:
    """
    Convert a book title into a safe folder name, e.g.:
      "Event-Driven Microservices with Kafka"
    -> "event-driven-microservices-with-kafka"
    """
    name = (name or "").strip().lower()
    # Replace any non-alphanumeric with a dash
    name = re.sub(r"[^a-z0-9]+", "-", name)
    # Remove leading/trailing dashes
    name = name.strip("-")
    return name or "untitled-book"

# ---------------------------------------------------------------------------
# AGENT DEFINITION
# ---------------------------------------------------------------------------

PLANNER_MODEL = Gemini(
              model="gemini-2.0-flash",
              retry_options=RETRY_CONFIG
              )  # same as other agents

root_agent = Agent(
    model=PLANNER_MODEL,
    name="planner_agent",
    description=(
        "Generates a complete 11-chapter structured outline for a technical book, "
        "including subsections with word targets and generation prompts."
    ),
    instruction="""
        You are a meticulous technical book outline designer.

        Your job: given a title, subtitle, topic, and audience, you must produce a
        COMPLETE, WELL-STRUCTURED PLAN for a technical book.

        INTERACTION RULES (IMPORTANT):

        1. On your **first response for a user request**, you MUST build the full plan
          JSON object and call the tool `emit_plan(plan={...})` exactly once.
        2. After the tool has been executed, ADK will give you the tool result.
          On your **next response**, you MUST:
          - Provide a short natural-language confirmation or summary of the plan
            (for example: number of chapters, the general flow).
          - You MUST NOT call `emit_plan` again.
        3. Do not start a new plan unless the user explicitly asks for a new one.

        DO NOT:
        - Call `emit_plan` more than once for the same user request.
        - Call any tools in your final confirmation message.
        - Loop or regenerate the plan repeatedly.

        OUTPUT FORMAT FOR emit_plan (first response only):

        You must call:

          emit_plan(plan={
            "title": "<book title>",
            "subtitle": "<book subtitle>",
            "metadata": {
              "topic": "<short topic>",
              "audience": "<short audience label>",
              "language": "en"
            },
            "chapters": [
              {
                "chapter_index": 1,
                "chapter_title": "<clear, specific chapter title>",
                "summary": "One sentence that describes the purpose of this chapter.",
                "subsections": [
                  {
                    "subsection_index": 1,
                    "title": "<subsection title>",
                    "brief": "One or two sentences describing what this subsection will cover.",
                    "word_target": 400,
                    "keywords": ["kw1", "kw2", "kw3"],
                    "generator_prompt": "A concise instruction the writer agent will use."
                  },
                  ...
                ]
              },
              ...
            ]
          })

        STRUCTURE RULES:
        - Exactly 11 chapters (indices 1 to 11).
        - Each chapter has 4–7 subsections.
        - Each subsection has: subsection_index, title, brief, word_target,
          keywords (length 3), generator_prompt.

        CONTENT GUIDELINES:
        - Chapter 1: introduction / motivation.
        - Middle chapters: core concepts, patterns, hands-on sections.
        - Final chapters: advanced topics, best practices, case studies, conclusion.
        - Avoid overlapping or redundant chapters.

        Remember:
        - First response → ONE `emit_plan` tool call with the full plan.
        - Second response → short text summary, NO tool calls.
        """,
    tools=[persist_plan],
)
