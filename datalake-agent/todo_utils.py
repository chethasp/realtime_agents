import json
from typing import Annotated
from pathlib import Path
from logging import getLogger

logger = getLogger(__name__)


def format_todo_str(data):
    todo_str = "Current todos:\n"
    for i, todo in enumerate(data):
        todo_str += f"{i + 1}. {todo['task']} ({todo['status']})\n"
    return todo_str


def get_data():
    try:
        with open(Path(__file__).parent / "todo.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    return data

def save_data(data):
    with open(Path(__file__).parent / "todo.json", "w") as f:
        json.dump(data, f, indent=4)



def add_todo(
    id: Annotated[int, "task id"],
    task: Annotated[str, "task description"],
    status: Annotated[str, "task status, either done or open"],
):
    # if exist, load the data
    # if not exist, create empty list
    data = get_data()
    data.append(
        {
            "id": id,
            "task": task,
            "status": status,
        }
    )
    save_data(data)
    return f"Todo with id {id} added.\n" + format_todo_str(data)


def modify_todo(
    id: Annotated[int, "task id"],
    task: Annotated[str, "task description"],
    status: Annotated[str, "task status, either done or open"],
) -> str:
    data = get_data()
    is_todo_found = False
    for todo in data:
        if todo["id"] == id:
            todo["task"] = task
            todo["status"] = status
            is_todo_found = True
            break

    if not is_todo_found:
        msg = f"Todo with id {id} not found."
        add_msg = add_todo(id, task, status)
        return msg + "\n" + add_msg

    save_data(data)
    return f"Todo with id {id} updated.\n" + format_todo_str(data)


def delete_todo(
    id: Annotated[int, "task id"],
    task: Annotated[str, "task description"],
    status: Annotated[str, "task status, either done or open"],
) -> str:
    logger.info(f"Deleting todo with id {id}, task {task}")
    data = get_data()

    is_todo_found = False
    new_data = []
    for todo in data:
        if todo["id"] == id:
            is_todo_found = True
        else:
            new_data.append(todo)

    data = new_data
    save_data(data)
    if is_todo_found:
        msg = f"Todo with id {id} deleted.\n" + format_todo_str(data)
    else:
        msg = f"Todo with id {id} not found. Nothing changed.\n" + format_todo_str(data)
    logger.info(f"Msg from delete: {msg}")
    return msg