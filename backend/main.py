from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://49.13.205.117:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://49.13.205.117:8000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://49.13.205.117:5000",
        "http://groceryghost-api.qubzes.com",
        "https://groceryghost-api.qubzes.com",
        "http://groceryghost.qubzes.com",
        "https://groceryghost.qubzes.com",
        "https://scrape-grocery-dash.lovable.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["scraper"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
