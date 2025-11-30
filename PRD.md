# **TechBook Author Agent – Product Requirements Document (Updated for Google ADK-only Architecture)**

## **1. Overview**

The **TechBook Author Agent** is a fully autonomous, production-ready **Google ADK (Agent Development Kit)** workflow for generating entire technical books end-to-end:

* SEO-optimized titles & subtitles
* 11-chapter structural outline
* Multi-agent coordinated chapter & subsection writing
* Markdown → formatted `.docx` assembly
* Back cover + SEO metadata generation

This system uses **exclusive Google ADK agentic architecture**:
every step (title generation, planning, writing, formatting, metadata) is handled by **independent ADK agents**, orchestrated by a top-level “supervisor agent”.

---

## **2. Updated Project Structure (as implemented)**

Based on your screenshot:

```
tech-book-agent/
│
├── agent.py                     # Main supervisor/orchestrator ADK agent
├── .env
│
├── sub-agents/
│   ├── title-agent.py           # ADK agent for SEO title/subtitle generation
│   ├── planner-agent.py         # ADK agent for chapter outline generation
│   ├── writer-agent.py          # ADK agent for subsection markdown writing
│   ├── docx-agent.py            # ADK agent for docx creation + markdown-to-docx
│   └── bookcover-agent.py       # ADK agent for back cover + SEO metadata
│
├── tools/
│   └── __init__.py             # reserved (optional local utilities)
│
├── docs/
│   └── PRD.md                   # This file
│
└── Reference/…                  # optional materials
```

**Key rule:**
▶️ *Every task must be implemented as a Google ADK agent.*
▶️ *No direct LLM SDK calls from Python.*
▶️ *All reasoning + operations happen inside ADK agent instructions + tools.*

---

## **3. System Design**

### **3.1 Multi-Agent Architecture**

The system contains **six ADK agents**:

| Agent                                      | Purpose                                                                       |
| ------------------------------------------ | ----------------------------------------------------------------------------- |
| **Supervisor Agent (`agent.py`)**          | Orchestrates the pipeline and calls sub-agents using ADK structured messages. |
| **Title Agent (`title-agent.py`)**         | Generates up to 10 SEO book titles & subtitles.                               |
| **Planner Agent (`planner-agent.py`)**     | Produces 11-chapter JSON outline with subsections.                            |
| **Writer Agent (`writer-agent.py`)**       | Writes markdown content for each subsection.                                  |
| **DOCX Agent (`docx-agent.py`)**           | Creates initial book DOCX and appends markdown into formatted DOCX.           |
| **BookCover Agent (`bookcover-agent.py`)** | Generates back cover text + SEO descriptions & keywords.                      |

---

## **4. Requirements (Updated for ADK-only Implementation)**

### **4.1 Title Agent Requirements**

* Input: topic or idea string
* Output (JSON):

  ```json
  [
    {"title": "...", "subtitle": "...", "seo_keywords": ["..","..",".."]}
  ]
  ```
* Must be implemented using **ADK Agent instructions only**.
* Should avoid copyrighted titles.
* Titles ≤ 8 words.
* Subtitles ≤ 1 short sentence.

---

### **4.2 Planner Agent Requirements**

* Input: title, subtitle, topic, audience
* Output JSON:

  ```json
  {
    "title": "...",
    "subtitle": "...",
    "chapters": [
      {
        "chapter_index": 1,
        "chapter_title": "...",
        "summary": "...",
        "subsections": [
          {
            "subsection_index": 1,
            "title": "...",
            "brief": "...",
            "word_target": 500,
            "keywords": ["..","..",".."],
            "generator_prompt": "..."
          }
        ]
      }
    ]
  }
  ```
* Must always return **exactly 11 chapters**.
* Each chapter has **4–7 subsections**.

---

### **4.3 Writer Agent Requirements**

* Accepts: chapter/subsection metadata
* Produces: high-quality **markdown** only
* Structure:

  * Heading: `### Subsection Title`
  * Bold terms: at least 2–3 terms
  * Fenced code blocks: ```lang
  * Tables in markdown when needed

Writer Agent must **use ADK agent responses**, not Python LLM calls.

---

### **4.4 DOCX Agent Requirements**

The DOCX agent is responsible for:

#### A. Creating initial DOCX file

* Title page
* Subtitle
* Author placeholder
* Table-of-contents placeholder
* Chapter placeholders

#### B. Appending markdown into formatted DOCX

* Convert markdown → HTML → DOCX
* Map headings to Heading styles
* Convert markdown bold → DOCX bold
* Convert code blocks → monospace
* Convert tables → DOCX tables

This must be implemented **inside ADK tools**, i.e.:

* Python tool transforms markdown → docx
* ADK agent decides *when* to call the tool

---

### **4.5 BookCover Agent Requirements**

Outputs JSON:

```json
{
  "blurb": "150-word marketing blurb",
  "author_tagline": "1-2 lines",
  "seo_description": "50-160 characters",
  "seo_keywords": ["kw1", "kw2", ..., "kw10"]
}
```

Must be generated purely via ADK agent instruction.

---

### **4.6 Supervisor Agent Requirements**

Coordinates everything:

1. User provides topic.
2. Supervisor calls Title Agent → user chooses one.
3. Supervisor calls Planner Agent → receives JSON outline.
4. Supervisor calls DOCX Agent → creates initial manuscript.
5. For each chapter/subsection:

   * Calls Writer Agent → markdown
   * Calls DOCX Agent → append markdown to docx
6. Calls BookCover Agent → receives metadata
7. Writes metadata into final DOCX

Supervisor handles:

* Logging
* Iterative LLM reasoning
* Flow-control
* Validation (JSON schema checks)
* Error recovery

---

## **5. Functional Requirements**

### **FR1 – Multi-Agent ADK System**

All agents must be implemented via **Google ADK**:

* each file creates a separate ADK `Agent` instance
* supervisor calls sub-agents using ADK “messages”

No direct SDK calls allowed outside ADK.

---

### **FR2 – Valid Schema Enforcement**

Each agent output is validated by the Supervisor Agent using JSON schemas defined in `agent.py`.

---

### **FR3 – Deterministic Workflow**

The pipeline must always:

1. Generate title options
2. Produce 11-chapter outline
3. Write subsections
4. Build docx
5. Produce publishing metadata

---

## **6. Non-Functional Requirements**

| Category        | Preference                                                       |
| --------------- | ---------------------------------------------------------------- |
| Reliability     | JSON schema validation, retry logic inside Supervisor            |
| Maintainability | Modular ADK agents in separate files                             |
| Extensibility   | New agents can be added easily                                   |
| Performance     | Gemini Flash 2.0 optimized for throughput                        |
| Observability   | Supervisor logs agent calls + responses                          |
| Quality         | Must avoid hallucinated facts, plagiarism, or duplicated content |

---

## **7. Tech Stack**

* **Google ADK** (core orchestrator)
* **Gemini 2.0 Flash** (LLM inside ADK)
* **python-docx** (formatting tools)
* **Markdown → HTML** conversion: `mistune`
* **HTML → DOCX**: via python-docx + BeautifulSoup

No external LLM SDK usage is allowed.

---

## **8. Agent Responsibilities Summary**

| Agent File                      | Responsibility                                     |
| ------------------------------- | -------------------------------------------------- |
| `agent.py`                      | Supervisor agent; orchestrates the entire pipeline |
| `sub-agents/title-agent.py`     | SEO title generator                                |
| `sub-agents/planner-agent.py`   | Outline & chapter planner                          |
| `sub-agents/writer-agent.py`    | Subsection markdown generator                      |
| `sub-agents/docx-agent.py`      | DOCX creation & markdown formatting                |
| `sub-agents/bookcover-agent.py` | Back cover blurb + SEO metadata                    |

---

## **9. End-to-End Flow**

```
User Topic
     ↓
Title Agent → 10 options → User selects
     ↓
Planner Agent → 11-chapter outline JSON
     ↓
DOCX Agent → create initial manuscript.docx
     ↓
Writer Agent → markdown for each subsection
DOCX Agent → append markdown into docx
(repeat for all chapters)
     ↓
BookCover Agent → SEO metadata + blurb
DOCX Agent → append blurb to end of manuscript
     ↓
Final Book (manuscript.docx)
```

---
