from fastapi import FastAPI
from pydantic import BaseModel

async def lifespan(app: FastAPI):
    # Startup event
    print("Starting up...")
    yield
    print("Shutting down...")
    # Shutdown event

app = FastAPI(title="SUCA API", lifespan=lifespan)

class Entry(BaseModel):
    id: int
    name: str
    description: str | None = None

@app.get("/health", tags=["Health"])
async def health_check() -> Entry:
    """
    Health check endpoint to verify that the API is running.
    """
    return Entry(id=1, name="Health Check", description="API is healthy")

