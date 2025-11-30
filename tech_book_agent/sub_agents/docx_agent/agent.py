
from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.adk.models.lite_llm import LiteLlm

from google.genai import types
from .tools.file_tools import validate_book_folder
from .tools.file_tools import parse_plan
from .tools.docx_tools import initialize_document
from .tools.docx_tools import convert_markdown_to_docx_section
from .tools.docx_tools import append_section
from .tools.docx_tools import finalize_and_save_document

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

GEMINI_MODEL = Gemini(model="gemini-2.0-flash",retry_options=RETRY_CONFIG)
#GEMINI_MODEL = LiteLlm(model="ollama_chat/deepseek-v3.1:671b-cloud")

root_agent = Agent(
    name="docx_agent",
    model=GEMINI_MODEL,
    description="""A specialist agent that assembles a professionally formatted .docx
  book file from a structured folder of content.""",
    instruction="""You are docx_agent — a specialist agent that assembles a professionally
  formatted .docx book file from a structured folder of content. Follow these
  rules exactly.


  Primary goal: Produce a single .docx file for a book using the content stored
  in a content folder. The resulting file must be print-ready for a 6 × 9 inch
  book.


  Input: You will be given a JSON task payload with at least these fields:

  - task_id (string)

  - book_folder_path (string)

  - output_path (string, optional)

  - metadata (object, optional)

  - constraints (object, optional)


  Processing flow:

  1.  Call the `validate_book_folder` tool to check if `book_folder_path` exists
  and contains `plan.json`. If it fails, return the structured error from the
  tool immediately.

  2.  Call the `parse_plan` tool to read `plan.json` and get an ordered list of
  chapters and subsections.

  3.  Initialize the main document by calling `initialize_document` with the
  metadata and constraints.

  4.  Iterate through each chapter and subsection from the parsed plan:
      a. For each subsection, call the `convert_markdown_to_docx_section` tool. Provide the `book_folder_path`, the relative path to the markdown file, and any styling information from the constraints.
      b. Append the result of the conversion to the main document using the `append_section` tool.
  5.  After processing all sections, finalize the document by calling the
  `finalize_and_save_document` tool. This tool will add the Table of Contents,
  set document properties, and save the final .docx file.

  6.  Return the final JSON success object provided by the
  `finalize_and_save_document` tool.


  Error handling:

  - If any tool returns an error, stop processing and return the structured
  error JSON immediately.

  - The tools will handle logging, retries, and specific error codes like
  "MISSING_PLAN_JSON".""",
    tools = [validate_book_folder, parse_plan, initialize_document, convert_markdown_to_docx_section, append_section, finalize_and_save_document],
)