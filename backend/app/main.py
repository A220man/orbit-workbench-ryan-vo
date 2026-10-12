"""FastAPI application factory and main entrypoint for Orbit Workbench."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.diagrams import router as diagrams_router
from app.api.evaluation import router as evaluation_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce security baseline: reject demo mode in production
    settings.check_production_safety()
    # Initialize database tables
    init_db()
    yield


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Editorial diagram design and agent visualization synthesis workbench",
        lifespan=lifespan,
    )

    # CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Healthcheck endpoint
    @application.get("/api/health", tags=["Health"])
    def health_check():
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
        }

    # Mount API routers
    application.include_router(diagrams_router, prefix="/api")
    application.include_router(evaluation_router, prefix="/api")
    application.include_router(auth_router, prefix="/api")
    application.include_router(audit_router, prefix="/api")

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
