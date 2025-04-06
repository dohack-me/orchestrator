from fastapi import FastAPI

from src.backend.main import OrchestratorBackendSingleton

app = FastAPI()
backend = OrchestratorBackendSingleton()

from src.frontend import routes

app.include_router(routes.ping.router)
app.include_router(routes.services.router)
app.include_router(routes.images.router)
