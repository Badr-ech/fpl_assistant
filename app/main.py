from fastapi import FastAPI
from app.routers import recommendations, captain, team_score, team

app = FastAPI(
    title="FPL Assistant API",
    description="API for Fantasy Premier League assistant providing recommendations, captain picks, and team optimization",
    version="0.1.0"
)

# Include routers
app.include_router(recommendations.router)
app.include_router(captain.router)
app.include_router(team_score.router)
app.include_router(team.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the FPL Assistant API"}
