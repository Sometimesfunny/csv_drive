from fastapi import FastAPI
from src.routers import auth, files

app = FastAPI()

app.include_router(auth.router)
app.include_router(files.router)
