from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import auth, inventory, rag, workflows

app = FastAPI(
    title="Pharma-Flow AI API",
    version="0.1.0",
    description="REST API for the Pharma-Flow AI multi-agent inventory MVP.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(rag.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "pharma-flow-api"}




