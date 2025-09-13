from fastapi import FastAPI

from router import health_check_router
from router import chat_completion_router
from router import analyze_resume_router

app = FastAPI()

app.include_router(health_check_router.router);
app.include_router(chat_completion_router.router);
app.include_router(analyze_resume_router.router);
