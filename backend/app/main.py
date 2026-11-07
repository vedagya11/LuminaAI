"""FastAPI application entrypoint."""

import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.schemas import RootResponse

logger = logging.getLogger("lumina")


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        summary="Classical low-light image restoration API.",
    )

    origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        if isinstance(exc, (HTTPException, RequestValidationError)):
            raise exc
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/", response_model=RootResponse, tags=["meta"])
    def root() -> RootResponse:
        return RootResponse(
            service=settings.app_name,
            health="/api/health",
            info="/api/info",
            docs="/docs",
        )

    app.include_router(router, prefix="/api")
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
