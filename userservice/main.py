from fastapi import FastAPI
from interface.api.controllers import user_controller

app = FastAPI()
app.include_router(user_controller.router)
