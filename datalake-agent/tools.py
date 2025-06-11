import json
from typing import Annotated, Dict, Any
from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)

QUESTIONS_FILE = Path(__file__).parent / "questions.json"
ANSWERS_FILE = Path(__file__).parent / "answers.json"

def get_questions() -> Dict[str, Dict[str, str]]:
    try:
        with open(QUESTIONS_FILE, "r") as f:
            questions = json.load(f)
    except FileNotFoundError:
        logger.error("questions.json not found")
        questions = {}
    return questions

def get_progress() -> Dict[str, Any]:
    try:
        with open(ANSWERS_FILE, "r") as f:
            progress = json.load(f)
    except FileNotFoundError:
        questions = get_questions()
        if not questions:
            return {"current_section": "", "current_question": "", "answers": {}}
        first_section = next(iter(questions))
        progress = {
            "current_section": first_section,
            "current_question": "1",
            "answers": {section: {str(i): None for i in range(1, len(questions[section]) + 1)} for section in questions}
        }
        save_progress(progress)
    return progress

def save_progress(progress: Dict[str, Any]) -> None:
    with open(ANSWERS_FILE, "w") as f:
        json.dump(progress, f, indent=4)

def get_current_question() -> str:
    progress = get_progress()
    questions = get_questions()
    section = progress["current_section"]
    question_num = progress["current_question"]
    if section in questions and question_num in questions[section]:
        return questions[section][question_num]
    return "No more questions available."

def save_answer(
    answer: Annotated[str, "user's answer to the current question"]
) -> str:
    progress = get_progress()
    questions = get_questions()
    section = progress["current_section"]
    question_num = progress["current_question"]

    # Save the answer
    progress["answers"][section][question_num] = answer

    # Advance to the next question or section
    section_questions = questions.get(section, {})
    next_question_num = str(int(question_num) + 1)
    if next_question_num in section_questions:
        progress["current_question"] = next_question_num
    else:
        # Move to the next section
        all_sections = list(questions.keys())
        current_index = all_sections.index(section)
        if current_index + 1 < len(all_sections):
            progress["current_section"] = all_sections[current_index + 1]
            progress["current_question"] = "1"
        else:
            # Exam complete
            progress["current_section"] = ""
            progress["current_question"] = ""
            save_progress(progress)
            return "Thank you for completing the intake exam."

    save_progress(progress)
    next_question = get_current_question()
    return f"Answer saved. Next question: {next_question}"

def skip_question() -> str:
    progress = get_progress()
    questions = get_questions()
    section = progress["current_section"]
    question_num = progress["current_question"]

    # Mark as skipped
    progress["answers"][section][question_num] = None

    # Advance to the next question or section
    section_questions = questions.get(section, {})
    next_question_num = str(int(question_num) + 1)
    if next_question_num in section_questions:
        progress["current_question"] = next_question_num
    else:
        all_sections = list(questions.keys())
        current_index = all_sections.index(section)
        if current_index + 1 < len(all_sections):
            progress["current_section"] = all_sections[current_index + 1]
            progress["current_question"] = "1"
        else:
            progress["current_section"] = ""
            progress["current_question"] = ""
            save_progress(progress)
            return "Thank you for completing the intake exam."

    save_progress(progress)
    next_question = get_current_question()
    return f"Question skipped. Next question: {next_question}"