from fastapi import FastAPI
from datasmith_agent.app.api.main_router import router

app = FastAPI(
    title="Interview Agentic Application",
    description="Assignment Task for DSAI Internship",
)

app.include_router(router)