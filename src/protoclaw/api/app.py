from fastapi import FastAPI

from protoclaw.api.routes import health, protocols, reviews


def create_app() -> FastAPI:
    application = FastAPI(
        title="Protoclaw",
        description="Sequencing protocol knowledge base API",
        version="0.1.0",
    )
    application.include_router(health.router)
    application.include_router(
        protocols.router, prefix="/protocols", tags=["protocols"]
    )
    application.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
    return application


app = create_app()
