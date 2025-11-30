"""
Confirm Content Agent (Google ADK)

Purpose:
  Called after writer-agent finishes (or during any stage), this agent verifies
  that every subsection listed in the persisted plan.json exists on disk under
  the book's chapters folder. If some subsections are missing, it returns a
  JSON list of missing subsections.

How it resolves the plan.json:
  - If 'plan_path' is provided and points to a file, use it.
  - Else if 'book_title' provided, slugify it and look for:
        <PROJECT_ROOT>/<slug>/plan.json
  - Else if 'file_url' provided and it's a local path to a plan.json, use it.
    (Developer note: you can pass local file path from UI as file_url; we'll
     transform it to a proper URL when making tool calls.)
  - Else, pick the most-recently-modified plan.json under project root.

Return shape:
{
  "plan_path": "...",
  "book_dir": "...",
  "expected_total_subsections": N,
  "found_subsections": M,
  "missing": [
    {
      "chapter_index": 1,
      "chapter_title": "Chapter title",
      "subsection_index": 2,
      "subsection_title": "Sub title",
      "expected_path": "...relative or absolute path..."
    },
    ...
  ]
}
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import re
import os

from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.adk.models.lite_llm import LiteLlm


# Project root is two parents up (tech-book-agent/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _slugify(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-") or "untitled-book"


def _find_latest_plan() -> Path:
    """
    Find the most recently modified plan.json under PROJECT_ROOT/*/plan.json
    """
    candidate_paths = list(PROJECT_ROOT.glob("*/plan.json"))
    if not candidate_paths:
        raise FileNotFoundError(f"No plan.json found under {PROJECT_ROOT}")
    latest_path = max(candidate_paths, key=lambda p: p.stat().st_mtime)
    return latest_path


def _resolve_plan_path(plan_path: Optional[str], book_title: Optional[str], file_url: Optional[str]) -> Path:
    """
    Resolve the plan.json Path in this order:
      1. plan_path argument (if exists)
      2. file_url if it points to a local plan.json file
      3. book_title -> PROJECT_ROOT/<slug>/plan.json
      4. latest plan.json under PROJECT_ROOT
    """
    # 1) direct plan_path
    if plan_path:
        p = Path(plan_path)
        if p.exists() and p.is_file():
            return p.resolve()

    # 2) file_url (developer note: local path may be supplied here)
    if file_url:
        p = Path(file_url)
        if p.exists() and p.is_file():
            return p.resolve()

    # 3) book_title
    if book_title:
        slug = _slugify(book_title)
        candidate = PROJECT_ROOT / slug / "plan.json"
        if candidate.exists():
            return candidate.resolve()

    # 4) fallback: latest
    return _find_latest_plan()


def _expected_subsection_path(book_dir: Path, chapter_index: int, subsection_index: int, subsection_title: str) -> Path:
    """
    Given plan info, compute expected markdown filepath:
      <book_dir>/chapters/chXX/subYY-<slug>.md
    """
    chapter_folder = book_dir / "chapters" / f"ch{chapter_index:02d}"
    sub_slug = _slugify(subsection_title)
    filename = f"sub{subsection_index:02d}-{sub_slug}.md"
    return chapter_folder / filename


# -----------------------------
# Function tool: check_subsections
# -----------------------------
def check_subsections(plan_path: Optional[str] = None,
                      book_title: Optional[str] = None,
                      file_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool callable by the agent.

    Parameters (all optional):
      - plan_path: direct path to a plan.json file
      - book_title: the book title used to find PROJECT_ROOT/<slug>/plan.json
      - file_url: a local path (or transformed URL) to the plan.json (developer may
                  pass the local upload path here; we'll resolve it)

    Returns:
      A dict containing missing subsections (if any), counts, and resolved paths.
    """
    # Resolve plan.json location
    try:
        resolved_plan = _resolve_plan_path(plan_path, book_title, file_url)
    except FileNotFoundError as e:
        return {"error": str(e), "plan_path_provided": plan_path, "book_title_provided": book_title, "file_url_provided": file_url}

    try:
        with resolved_plan.open("r", encoding="utf-8") as f:
            plan = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load plan.json at {resolved_plan}: {e}"}

    # Determine book_dir (where planner persisted things)
    book_dir = resolved_plan.parent

    missing: List[Dict[str, Any]] = []
    found_count = 0
    expected_total = 0

    chapters = plan.get("chapters", [])
    for c in chapters:
        try:
            ch_idx = int(c.get("chapter_index", 0))
        except Exception:
            ch_idx = 0
        ch_title = c.get("chapter_title", f"Chapter {ch_idx}")
        subsections = c.get("subsections", [])
        for s in subsections:
            try:
                sub_idx = int(s.get("subsection_index", 0))
            except Exception:
                sub_idx = 0
            sub_title = s.get("title", f"Subsection {sub_idx}")
            expected_total += 1
            expected_path = _expected_subsection_path(book_dir, ch_idx, sub_idx, sub_title)
            if expected_path.exists():
                found_count += 1
            else:
                missing.append({
                    "chapter_index": ch_idx,
                    "chapter_title": ch_title,
                    "subsection_index": sub_idx,
                    "subsection_title": sub_title,
                    "expected_path": str(expected_path)
                })

    result = {
        "plan_path": str(resolved_plan),
        "book_dir": str(book_dir),
        "expected_total_subsections": expected_total,
        "found_subsections": found_count,
        "missing_count": len(missing),
        "missing": missing,
    }
    return result

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

#GEMINI_MODEL = Gemini( model="gemini-2.0-flash",retry_options=RETRY_CONFIG)  # same as other agents
GEMINI_MODEL = LiteLlm(model="ollama_chat/deepseek-v3.1:671b-cloud")

# -----------------------------
# Agent definition (ADK)
# -----------------------------
root_agent = Agent(
    name="confirm_content_agent",
    model=GEMINI_MODEL,
    description="Verifies that all subsections specified in plan.json exist on disk; outputs any missing subsections.",
    instruction="""
You are ConfirmContentAgent. Your job is to check whether every subsection described
in the persisted plan.json for a book exists as a markdown file on disk.

INPUT: The user will provide one of:
  - plan_path (direct path to plan.json), OR
  - book_title (book's title), OR
  - file_url (a local path or URL pointing to plan.json).

RESPONSE RULES:
  1) Resolve the plan.json as described and then call the tool `check_subsections` exactly once with the resolved reference.
  2) Return ONLY the tool's resulting JSON. Do not add commentary.
  3) If you cannot find any plan.json, return an error map from the tool.

Example of a UI-provided local path you can accept as file_url:
  /mnt/data/207f08fa-60a6-48ad-be33-30f86df50b2a.png

When invoked, call: check_subsections(plan_path=<...> or book_title=<...> or file_url=<...>)
and return the tool output.
""",
    tools=[check_subsections],
)
