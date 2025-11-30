import os
import json
from typing import Dict, Any, List

def validate_book_folder(book_folder_path: str) -> Dict[str, Any]:
    """
    Validates that the book folder path exists and contains a 'plan.json' file.

    Args:
        book_folder_path: The absolute path to the book's root folder.

    Returns:
        A dictionary with the status of the validation.
    """
    if not os.path.isdir(book_folder_path):
        return {
            "status": "error",
            "error_code": "BOOK_FOLDER_NOT_FOUND",
            "message": f"The specified directory does not exist: {book_folder_path}"
        }

    plan_path = os.path.join(book_folder_path, "plan.json")
    if not os.path.isfile(plan_path):
        return {
            "status": "error",
            "error_code": "MISSING_PLAN_JSON",
            "message": f"'plan.json' not found in the root of the book folder: {book_folder_path}"
        }

    return {"status": "success", "message": "Book folder and plan.json validated successfully."}


def parse_plan(book_folder_path: str) -> Dict[str, Any]:
    """
    Parses the plan.json file to produce an ordered list of chapters and subsections.

    Args:
        book_folder_path: The absolute path to the book's root folder.

    Returns:
        A dictionary containing the parsed plan or an error.
    """
    plan_path = os.path.join(book_folder_path, "plan.json")
    try:
        with open(plan_path, 'r') as f:
            plan_data = json.load(f)

        # Basic validation of plan structure
        if "chapters" not in plan_data or not isinstance(plan_data["chapters"], list):
             return {
                "status": "error",
                "error_code": "INVALID_PLAN_JSON",
                "message": "'plan.json' is missing the 'chapters' list."
            }

        return {
            "status": "success",
            "plan": plan_data
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "error_code": "MALFORMED_PLAN_JSON",
            "message": "Failed to parse 'plan.json' due to a syntax error."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "PLAN_PARSING_FAILED",
            "message": f"An unexpected error occurred while parsing plan.json: {e}"
        }
