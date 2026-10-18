"""Demo server: serves the FastAPI backend AND the built React frontend on ONE port,
so a single public link covers the whole project. Does not modify backend/main.py."""
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.main import app as api_app  # noqa: F401  (import for side-effect: routes registered)

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

app: FastAPI = api_app

if os.path.isdir(DIST):
    # Serve built assets
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def _root():
        return FileResponse(os.path.join(DIST, "index.html"))

    # SPA fallback: any non-API GET route serves index.html (React Router handles it)
    @app.get("/{path:path}", include_in_schema=False)
    def _spa(path: str):
        if path.startswith("api/") or path.startswith("ws/"):
            return {"detail": "not found"}
        f = os.path.join(DIST, path)
        if os.path.isfile(f):
            return FileResponse(f)
        return FileResponse(os.path.join(DIST, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def _no_dist():
        return {"detail": "frontend/dist not built - API only"}
