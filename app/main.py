from fastapi import FastAPI

from app.api.routes.links import redirect_router, router as links_router


app = FastAPI(title="url shortener", version="1.0.0")

app.include_router(links_router, prefix="/api/v1")
app.include_router(redirect_router)