"""
ReCare AI - Reports, Exports & Impact Estimation API Router
Provides downloadable CSV and PDF Monday Morning Care Coordination Briefs,
and interactive Readmission Aversion Impact Sensitivity models.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.api.call_list import get_current_call_list
from backend.services.report_service import generate_call_list_csv, generate_call_list_pdf
from backend.services.impact_estimator import calculate_impact_scenarios

router = APIRouter(prefix="/api/reports", tags=["Reports & Exports"])


@router.get("/call-list.csv")
def download_call_list_csv(db: Session = Depends(get_db)):
    """Generate and download the Monday Morning Care Coordination Brief in CSV format."""
    call_list_data = get_current_call_list(db)
    csv_content = generate_call_list_csv(call_list_data)

    filename = f"ReCare_Call_List_{call_list_data.get('call_list_id', 'current')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/call-list.pdf")
def download_call_list_pdf(db: Session = Depends(get_db)):
    """Generate and stream the professional Monday Morning Care Coordination Brief PDF."""
    try:
        call_list_data = get_current_call_list(db)
        pdf_bytes = generate_call_list_pdf(call_list_data)

        filename = f"ReCare_Care_Brief_{call_list_data.get('call_list_id', 'current')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")


@router.get("/impact-analysis")
def get_impact_analysis(
    cohort_size: int = Query(50, ge=1, le=500),
    avg_risk: float = Query(0.42, ge=0.01, le=1.0),
):
    """Calculate readmission aversion impact estimates with conservative, central, and optimistic scenarios."""
    scenarios = calculate_impact_scenarios(
        selected_patients_count=cohort_size,
        average_readmission_risk=avg_risk,
    )
    return scenarios
