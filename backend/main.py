from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import strategies, ai, simulation, data, greeks, files, backtest_api, margin, ai_evaluation, analytics

app = FastAPI(
    title="HyperQuant AI Backend",
    description="Professional Options Quant Platform API",
    version="0.2.1"
)

# Trigger reload 2

# CORS configuration
origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategies.router)
app.include_router(ai.router)
app.include_router(simulation.router)
app.include_router(data.router)
app.include_router(greeks.router)
app.include_router(files.router)
app.include_router(backtest_api.router)
app.include_router(margin.router)
app.include_router(ai_evaluation.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    return {"message": "HyperQuant AI Backend Operational", "status": "online"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
