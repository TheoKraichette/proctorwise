from fastapi import FastAPI
from interface.api.controllers import reservation_controller

app = FastAPI()
app.include_router(reservation_controller.router)
