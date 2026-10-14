"""
ReCare AI - FastAPI Backend Application Entrypoint
Predict Earlier. Prioritize Smarter. Prevent Avoidable Readmissions.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine, Base
from backend.api import (
    dashboard,
    patients,
    predictions,
    call_list,
    evaluation,
    fairness,
    datasets,
    reports,
    model_info,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ReCare AI",
    description=(
        "AI-Powered 30-Day Hospital Readmission Prediction & Care Intervention Platform. "
        "Predict Earlier. Prioritize Smarter. Prevent Avoidable Readmissions."
    ),
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(dashboard.router)
app.include_router(patients.router)
app.include_router(predictions.router)
app.include_router(call_list.router)
app.include_router(evaluation.router)
app.include_router(fairness.router)
app.include_router(datasets.router)
app.include_router(reports.router)
app.include_router(model_info.router)


@app.on_event("startup")
def on_startup():
    """Ensure database schema and initial seed data are initialized on startup."""
    logger.info("Verifying database schema...")
    Base.metadata.create_all(bind=engine)
    try:
        from backend.db.init_db import initialize_and_seed_database
        initialize_and_seed_database()
    except Exception as e:
        logger.warning(f"Database seed notice: {e}")
    logger.info("ReCare AI backend services initialized.")


@app.get("/health")
def health_check():
    """System health check endpoint."""
    model_exists = os.path.exists("backend/models/recare_readmission_model.joblib")
    return {
        "status": "healthy",
        "service": "ReCare AI Backend",
        "version": "1.2.0",
        "model_loaded": model_exists,
        "database_connected": True,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "Synthetic-data clinical decision support prototype.",
    }


@app.get("/")
def root():
    """Root platform information."""
    return {
        "name": "ReCare AI",
        "tagline": "Predict Earlier. Prioritize Smarter. Prevent Avoidable Readmissions.",
        "weekly_contact_capacity": 50,
        "api_documentation": "/docs",
        "health_check": "/health",
        "disclaimer": (
            "ReCare AI is a synthetic-data demonstration of clinical decision support. "
            "Its predictions and intervention suggestions are not validated for clinical use "
            "and must not replace professional judgment."
        ),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
