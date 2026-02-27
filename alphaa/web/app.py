"""FastAPI application factory and entry point."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from alphaa.web.routes import router

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path("~/.alphaa/web/static").expanduser()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="AlphaA")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    app.include_router(router)
    return app


def main() -> None:
    """Run the web server."""
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
