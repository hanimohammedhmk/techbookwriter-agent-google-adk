# -------------------------
# Fix-Missing Agent: confirm-as-subagent + writer agents for missing subsections
# -------------------------
import json
import re
import uuid

from pathlib import Path
from typing import Any, Dict, List, Optional

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.models.lite_llm import LiteLlm

from google.genai import types

RETRY_CONFIG = types.HttpRetryOptions(
    attempts=10,
    exp_base=7,
    initial_delay=2,
    http_status_codes=[
        429,
        500,
        503,
        504,
    ],
)

#GEMINI_MODEL = Gemini(model="gemini-2.0-flash",retry_options=RETRY_CONFIG)
GEMINI_MODEL = LiteLlm(model="ollama_chat/deepseek-v3.1:671b-cloud")

# Project root is 3 levels up from here: sub-agents/fix_missing_agent/agent.py -> sub-agents -> tech-book-agent -> root
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _slugify(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-") or "untitled-book"


def _find_latest_plan() -> Dict[str, Any]:
    """
    Discover the most recently modified plan.json under tech-book-agent/*/plan.json.
    """
    candidate_paths = list(PROJECT_ROOT.glob("*/plan.json"))
    if not candidate_paths:
        return {}

    latest_path = max(candidate_paths, key=lambda p: p.stat().st_mtime)
    try:
        with latest_path.open("r", encoding="utf-8") as f:
            plan = json.load(f)

        book_dir = latest_path.parent
        plan.setdefault("storage", {})
        plan["storage"].setdefault("book_dir", str(book_dir))
        plan["storage"].setdefault("plan_path", str(latest_path))
        return plan
    except Exception:
        return {}


# Load plan context
PLAN = _find_latest_plan()
BOOK_TITLE = PLAN.get("title", "Untitled Book")
BOOK_SUBTITLE = PLAN.get("subtitle", "")
BOOK_SLUG = _slugify(BOOK_TITLE)
BOOK_DIR_STR = PLAN.get("storage", {}).get("book_dir", "")
BOOK_DIR = Path(BOOK_DIR_STR) if BOOK_DIR_STR else (PROJECT_ROOT / BOOK_SLUG)

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

def persist_subsection(
    book_slug: str,
    chapter_index: int,
    subsection_index: int,
    subsection_title: str,
    markdown: str,
) -> Dict[str, Any]:
    """
    Persist a single subsection's markdown content to disk.
    """
    slug = _slugify(book_slug)
    base_dir = BOOK_DIR if BOOK_DIR.exists() else (PROJECT_ROOT / slug)

    chapter_folder = base_dir / "chapters" / f"ch{chapter_index:02d}"
    chapter_folder.mkdir(parents=True, exist_ok=True)

    sub_slug = _slugify(subsection_title)
    filename = f"sub{subsection_index:02d}-{sub_slug}.md"
    file_path = chapter_folder / filename

    with file_path.open("w", encoding="utf-8") as f:
        f.write(markdown)

    return {
        "book_slug": slug,
        "chapter_index": chapter_index,
        "subsection_index": subsection_index,
        "path": str(file_path),
    }

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


def build_confirm_agent(plan_path: str = None, file_url: str = None, book_title: str = None) -> LlmAgent:
    """
    Produce a fresh confirm LlmAgent instance that will call check_subsections(...) exactly once.
    """
    if plan_path:
        arg_expr = f'plan_path="{plan_path}"'
    elif file_url:
        arg_expr = f'file_url="{file_url}"'
    elif book_title:
        arg_expr = f'book_title="{book_title}"'
    else:
        arg_expr = ""

    instruction = f"""
    Call the tool `check_subsections({arg_expr})` and return the raw JSON response.
    """

    return LlmAgent(
        name=f"confirm_before_{uuid.uuid4().hex[:6]}",
        model=GEMINI_MODEL,
        instruction=instruction,
        tools=[],
    )


def build_writer_agent_for_missing(
    chapter_index: int,
    chapter_title: str,
    subsection_index: int,
    subsection_title: str,
    brief: str = "",
    generator_prompt: str = "",
    word_target: int = 600,
) -> LlmAgent:
    """
    Build an LlmAgent that writes one missing subsection and persists it by calling persist_subsection(...) exactly once.
    """
    instruction = f"""
You are a professional technical book author.

Book title: "{BOOK_TITLE}"
Chapter {chapter_index}: "{chapter_title}"
Subsection {subsection_index}: "{subsection_title}"

Brief:
{brief}

Generator prompt:
{generator_prompt}

Target length: around {word_target} words.

RULES:
- Output ONLY the subsection content in **markdown**.
- Use headings, short paragraphs, bullet lists, and **bold** for key terms.
- Use fenced code blocks for any code.
- AFTER generating the markdown, CALL the function persist_subsection exactly once with this exact signature:
  persist_subsection(
      book_slug="{BOOK_SLUG}",
      chapter_index={chapter_index},
      subsection_index={subsection_index},
      subsection_title="{subsection_title}",
      markdown=<the markdown you just generated>
  )
- Do NOT print any other text outside the tool call.
- Do NOT call any other tools.
"""
    return LlmAgent(
        name=f"repair_ch{chapter_index:02d}_sub{subsection_index:02d}_{uuid.uuid4().hex[:6]}",
        model=GEMINI_MODEL,
        instruction=instruction,
        description=f"Write and persist subsection {subsection_index} of chapter {chapter_index}",
        tools=[persist_subsection],
    )


# Build runtime list of missing subsections by calling the confirm tool synchronously.
# This gives us the set of repair agents to attach as subagents of the SequentialAgent.
# Prefer the persisted plan path from PLAN if available.
_plan_path = PLAN.get("storage", {}).get("plan_path")
_confirm_resp = None
try:
    # call the check_subsections tool directly to learn current missing items
    if _plan_path:
        _confirm_resp = check_subsections(plan_path=_plan_path)
    elif PLAN:
        _confirm_resp = check_subsections(book_title=BOOK_TITLE)
    else:
        _confirm_resp = check_subsections()
except Exception:
    _confirm_resp = None

missing_items: List[dict] = []
if isinstance(_confirm_resp, dict):
    # tool returns {"missing": [...], ...} per confirm agent implementation
    missing_items = _confirm_resp.get("missing", [])

# Build repair agents for each missing item
repair_agents: List[LlmAgent] = []
for m in missing_items:
    ch_idx = int(m.get("chapter_index", 0))
    ch_title = m.get("chapter_title", f"Chapter {ch_idx}")
    sub_idx = int(m.get("subsection_index", 0))
    sub_title = m.get("subsection_title", f"Subsection {sub_idx}")

    # obtain subsection metadata from PLAN to populate brief/generator_prompt/word_target
    subsection_meta = {}
    for ch in PLAN.get("chapters", []):
        if int(ch.get("chapter_index", 0)) == ch_idx:
            for s in ch.get("subsections", []):
                if int(s.get("subsection_index", 0)) == sub_idx:
                    subsection_meta = s
                    break
            break

    repair_agents.append(
        build_writer_agent_for_missing(
            chapter_index=ch_idx,
            chapter_title=ch_title,
            subsection_index=sub_idx,
            subsection_title=sub_title,
            brief=subsection_meta.get("brief", ""),
            generator_prompt=subsection_meta.get("generator_prompt", ""),
            word_target=subsection_meta.get("word_target", 600),
        )
    )

# Build fresh confirm agents to run before and after repairs as subagents
confirm_before = build_confirm_agent(plan_path=_plan_path)
confirm_after = build_confirm_agent(plan_path=_plan_path)

# Compose the root SequentialAgent: confirm_before -> repair_agents... -> confirm_after
if not repair_agents:
    # nothing to repair; a simple agent to indicate completion
    done_agent = LlmAgent(
        name=f"nothing_to_fix_{uuid.uuid4().hex[:6]}",
        model=GEMINI_MODEL,
        instruction='No missing subsections detected. Reply with the exact text: "ALL SUBSECTIONS PRESENT".',
        tools=[],
    )
    root_agent = SequentialAgent(
        name=f"fix_missing_pipeline_{uuid.uuid4().hex[:6]}",
        sub_agents=[confirm_before, done_agent],
        description="Checks for missing subsections and reports that none are missing."
    )
else:
    seq_subs = [confirm_before] + repair_agents + [confirm_after]
    root_agent = SequentialAgent(
        name=f"fix_missing_pipeline_{uuid.uuid4().hex[:6]}",
        sub_agents=seq_subs,
        description=f"Repairs {len(repair_agents)} missing subsections found during initialization."
    )
