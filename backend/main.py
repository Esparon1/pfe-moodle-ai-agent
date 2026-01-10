from fastapi import FastAPI
from app.db.init_db import init_db
from app.api.analytics_routes import router as analytics_router
from app.api.platform_routes import router as platform_router
from app.api.me_routes import router as me_router #Testing x User id

app = FastAPI(title="PFE Mini-Moodle")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(analytics_router)
app.include_router(platform_router)
app.include_router(me_router)
