from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, List

from app.models.database import get_db
from app.services.metrics_service import MetricsService
from app.services.attribution_service import AttributionService
from app.services.optimization_service import OptimizationService

load_dotenv()

app = FastAPI(
    title="MMM Platform API",
    description="Marketing Mix Modeling Platform for ROI optimization",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class OptimizationRequest(BaseModel):
    total_budget: float
    constraints: Optional[Dict] = None

class ScenarioRequest(BaseModel):
    scenarios: List[Dict]

@app.get("/")
def root():
    return {
        "message": "MMM Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/metrics/overview")
async def get_overview_metrics(start_date: str, end_date: str, db: Session = Depends(get_db)):
    """
    Returns:
    - Total spend
    - Total revenue  
    - Overall ROAS
    - Channel breakdown
    - Period-over-period comparison
    """
    metrics_service = MetricsService(db)
    return metrics_service.get_overview_metrics(start_date, end_date)

@app.get("/api/channels/{channel}/performance")
async def get_channel_performance(channel: str, start_date: str, end_date: str, db: Session = Depends(get_db)):
    """
    Returns:
    - Spend over time
    - Revenue contribution
    - ROI curve (diminishing returns)
    - Best performing periods
    - Optimization opportunities
    """
    metrics_service = MetricsService(db)
    return metrics_service.get_channel_performance(channel, start_date, end_date)

@app.get("/api/channels/{channel}/trends")
async def get_channel_trends(channel: str, days: int = 30, db: Session = Depends(get_db)):
    """Get recent trends for a specific channel"""
    metrics_service = MetricsService(db)
    return metrics_service.get_channel_trends(channel, days)

@app.post("/api/optimize")
async def optimize_budget(request: OptimizationRequest, db: Session = Depends(get_db)):
    """
    Allocate budget to maximize total revenue
    using marginal ROAS equalization
    """
    optimization_service = OptimizationService(db)
    return optimization_service.optimize_budget(request.total_budget, request.constraints)

@app.post("/api/optimize/scenarios")
async def simulate_scenarios(request: ScenarioRequest, db: Session = Depends(get_db)):
    """Simulate multiple budget scenarios"""
    optimization_service = OptimizationService(db)
    return optimization_service.simulate_scenarios(request.scenarios)

@app.get("/api/optimize/diminishing-returns")
async def get_diminishing_returns(db: Session = Depends(get_db)):
    """Analyze diminishing returns for each channel"""
    optimization_service = OptimizationService(db)
    return optimization_service.get_diminishing_returns_analysis()

@app.get("/api/attribution/models")
async def get_attribution_models():
    """List available attribution models"""
    return {
        "models": [
            {"id": "last_click", "name": "Last Click", "description": "100% credit to last touchpoint"},
            {"id": "linear", "name": "Linear", "description": "Equal credit to all touchpoints"},
            {"id": "time_decay", "name": "Time Decay", "description": "More credit to recent touchpoints"},
            {"id": "u_shaped", "name": "U-Shaped", "description": "40% first, 40% last, 20% middle"},
            {"id": "data_driven", "name": "Data-Driven", "description": "ML-based attribution"}
        ]
    }

@app.get("/api/attribution/calculate")
async def calculate_attribution(start_date: str, end_date: str, model: str = "linear", db: Session = Depends(get_db)):
    """Calculate attribution for a given period and model"""
    attribution_service = AttributionService(db)
    return attribution_service.calculate_attribution(start_date, end_date, model)

@app.get("/api/attribution/compare")
async def compare_attribution_models(start_date: str, end_date: str, db: Session = Depends(get_db)):
    """Compare results across different attribution models"""
    attribution_service = AttributionService(db)
    return attribution_service.compare_attribution_models(start_date, end_date)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)