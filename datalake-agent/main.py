from contextlib import asynccontextmanager
from logging import getLogger
from pathlib import Path

import autogen
from autogen.agentchat.realtime_agent import RealtimeAgent, WebSocketAudioAdapter
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .tools import get_current_question, get_progress, save_answer, skip_question, get_questions
import time

realtime_config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location=str(Path(__file__).parent.parent),
    filter_dict={
        "tags": ["gpt-4o-mini-realtime"],
    },
)

realtime_llm_config = {
    "timeout": 600,
    "config_list": realtime_config_list,
    "temperature": 0.8,
}

app = FastAPI()

@asynccontextmanager
async def lifespan(*args, **kwargs):
    print(
        "Application started. Please visit http://localhost:5050/start-chat to start the intake exam."
    )
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=JSONResponse)
async def index_page() -> dict[str, str]:
    return {"message": "Intake Exam Voice Agent is running!"}

website_files_path = Path(__file__).parent / "website_files"

app.mount(
    "/static", StaticFiles(directory=website_files_path / "static"), name="static"
)

templates = Jinja2Templates(directory=website_files_path / "templates")

@app.get("/start-chat/", response_class=HTMLResponse)
async def start_chat(request: Request) -> HTMLResponse:
    port = request.url.port
    return templates.TemplateResponse("chat.html", {"request": request, "port": port})

@app.get("/progress")
def get_current_progress():
    return get_progress()

@app.get("/questions")
def get_all_questions():
    return get_questions()

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket) -> None:
    await websocket.accept()

    logger = getLogger("uvicorn.error")
    audio_adapter = WebSocketAudioAdapter(websocket, logger=logger)

    progress = get_progress()
    current_question = get_current_question()
    system_message = f"""You are an AI voice assistant for an intake exam, powered by AG2 and the OpenAI Realtime API.
You will ask questions one at a time from a predefined set, track progress, and save user answers.

- Current section: {progress['current_section']}
- Current question number: {progress['current_question']}
- Current question: {current_question}
- Ask the current question and wait for the user's response.
- Call the `save_answer` function with the user's response to save it and advance to the next question.
- If the user says "skip" or "I don't know," call the `skip_question` function to skip the question and advance.
- If the response is unclear, repeat the current question.
- Do not ask multiple questions at once. Focus only on the current question.
- When all questions are complete, inform the user: "Thank you for completing the intake exam."
"""
    system_message += "\nCurrent date and time: " + time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()
    )

    realtime_agent = RealtimeAgent(
        name="Intake Exam Bot",
        system_message=system_message,
        llm_config=realtime_llm_config,
        audio_adapter=audio_adapter,
        logger=logger,
    )

    realtime_agent.register_realtime_function(
        name="save_answer", description="Save the user's answer and advance"
    )(save_answer)

    realtime_agent.register_realtime_function(
        name="skip_question", description="Skip the current question and advance"
    )(skip_question)

    await realtime_agent.run()