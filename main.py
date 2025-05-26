import uvicorn
from fastapi import FastAPI
from app.routers import recommendations, captain, team_score
from app.utils.logger import setup_logger

# Set up logger
logger = setup_logger("fpl_assistant")

app = FastAPI(
    title="FPL Assistant API",
    description="API for Fantasy Premier League assistant providing recommendations, captain picks, and team optimization",
    version="0.1.0"
)

# Include routers
app.include_router(recommendations.router)
app.include_router(captain.router)
app.include_router(team_score.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the FPL Assistant API"}


if __name__ == "__main__":
    logger.info("Starting FPL Assistant API")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
