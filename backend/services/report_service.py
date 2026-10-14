"""
ReCare AI - Report Generation Engine
Generates Monday Morning Care Coordination Brief in CSV and formatted PDF formats.
"""

import io
import os
import csv
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

logger = logging.getLogger(__name__)


def generate_call_list_csv(call_list_payload: Dict[str, Any]) -> str:
    """Generate RFC-4180 compliant CSV string of the prioritized 50-patient call list."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header metadata rows
    writer.writerow(["# ReCare AI - Monday Morning Care Coordination Brief"])
    writer.writerow(["# Call List ID", call_list_payload.get("call_list_id", "N/A")])
    writer.writerow(["# Reporting Period", call_list_payload.get("reporting_period", "N/A")])
    writer.writerow(["# Generated At", call_list_payload.get("generated_at", "N/A")])
    writer.writerow(["# Ranking Mode", call_list_payload.get("ranking_mode", "N/A")])
    writer.writerow(["# Capacity Constraint", f"{call_list_payload.get('selected_count', 0)} / {call_list_payload.get('capacity_limit', 50)}"])
    writer.writerow([])

    # Table columns
    columns = [
        "Priority Rank",
        "Patient ID",
        "Encounter ID",
        "Age",
        "Sex",
        "Payer Type",
        "Primary Condition",
        "Discharge Disposition",
        "Calibrated Risk %",
        "Risk Tier",
        "Expected Benefit %",
        "Recommended Intervention",
        "Intervention Priority",
        "Primary Action Plan",
        "Top Risk Drivers",
        "Contact Status",
        "Follow-up Notes",
    ]
    writer.writerow(columns)

    for p in call_list_payload.get("selected_patients", []):
        drivers_text = "; ".join([d.get("feature_label", "") for d in p.get("key_risk_drivers", [])])
        writer.writerow([
            p.get("rank"),
            p.get("patient_id"),
            p.get("encounter_id"),
            p.get("age"),
            p.get("sex"),
            p.get("payer_type"),
            p.get("condition_name"),
            p.get("discharge_disposition"),
            p.get("risk_percentage"),
            p.get("risk_category"),
            p.get("expected_benefit_percentage"),
            p.get("recommended_intervention"),
            p.get("intervention_priority"),
            p.get("intervention_action_plan"),
            drivers_text,
            p.get("contact_status", "Pending"),
            p.get("follow_up_notes", ""),
        ])

    return output.getvalue()


def generate_call_list_pdf(call_list_payload: Dict[str, Any]) -> bytes:
    """
    Generate professional multi-page executive PDF report using ReportLab.
    Includes Executive Summary Dashboard card + Prioritized Patient Roster with Contact Status checkboxes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_navy = colors.HexColor("#0f172a")
    c_teal = colors.HexColor("#0d9488")
    c_slate = colors.HexColor("#475569")
    c_light_bg = colors.HexColor("#f8fafc")
    c_border = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=c_navy,
    )
    
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_slate,
    )

    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=c_navy,
    )

    cell_normal = ParagraphStyle(
        "CellNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=c_slate,
    )

    cell_disclaimer = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#64748b"),
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("ReCare AI — Monday Morning Care Coordination Brief", title_style))
    reporting_period = call_list_payload.get("reporting_period", f"Week {datetime.now().isocalendar()[1]}")
    mode_text = call_list_payload.get("mode_description", "Mode A: Calibrated Risk Priority")
    story.append(Paragraph(f"Reporting Period: <b>{reporting_period}</b> | Generated: {datetime.now().strftime('%b %d, %Y %H:%M')} | {mode_text}", subtitle_style))
    story.append(Spacer(1, 10))

    # Executive Summary Metric Cards Table
    summary = call_list_payload.get("summary", {})
    selected_cnt = call_list_payload.get("selected_count", 0)
    total_eligible = call_list_payload.get("total_eligible_discharges", 0)
    avg_risk = summary.get("average_selected_risk", 0.0)
    cohort_avg = summary.get("cohort_average_risk", 0.0)
    enrichment = summary.get("risk_enrichment_ratio", 1.0)
    est_averted = summary.get("estimated_readmissions_averted_illustrative", 0.0)

    summary_data = [
        [
            Paragraph(f"<b>Weekly Contact Cap:</b><br/>{selected_cnt} / 50 Unique Pts", cell_normal),
            Paragraph(f"<b>Eligible Discharges:</b><br/>{total_eligible} Encounter Records", cell_normal),
            Paragraph(f"<b>Selected Cohort Avg Risk:</b><br/><b>{avg_risk*100:.1f}%</b> (Cohort: {cohort_avg*100:.1f}%)", cell_normal),
            Paragraph(f"<b>Enrichment Ratio:</b><br/><b>{enrichment:.1f}x</b> Baseline", cell_normal),
            Paragraph(f"<b>Est. Readmissions Averted:</b><br/>~<b>{est_averted:.1f}</b> (Illustrative)", cell_normal),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[140, 140, 160, 130, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # Table of Selected Patients
    table_headers = [
        Paragraph("<b>Rank</b>", cell_bold),
        Paragraph("<b>Patient & Encounter</b>", cell_bold),
        Paragraph("<b>Demographics</b>", cell_bold),
        Paragraph("<b>Primary Condition</b>", cell_bold),
        Paragraph("<b>Risk & Benefit</b>", cell_bold),
        Paragraph("<b>Recommended Intervention</b>", cell_bold),
        Paragraph("<b>Primary Action Plan</b>", cell_bold),
        Paragraph("<b>Contact Status</b>", cell_bold),
    ]

    patient_rows = [table_headers]
    for p in call_list_payload.get("selected_patients", []):
        pt_info = f"<b>{p.get('patient_id')}</b><br/>{p.get('encounter_id')}"
        demo_info = f"{p.get('age', 'N/A')}yo {p.get('sex', '')}<br/>{p.get('payer_type', '')}"
        cond_info = f"<b>{p.get('condition_name')}</b><br/>{p.get('discharge_disposition', '')}"
        risk_info = f"<b>{p.get('risk_percentage')}%</b> Risk<br/>+{p.get('expected_benefit_percentage', 0)}% Benefit"
        interv_info = f"<b>{p.get('recommended_intervention')}</b><br/><i>[{p.get('intervention_priority')} Priority]</i>"
        action_info = p.get('intervention_action_plan', '')
        status_info = f"[  ] {p.get('contact_status', 'Pending')}"

        patient_rows.append([
            Paragraph(f"<b>#{p.get('rank')}</b>", cell_bold),
            Paragraph(pt_info, cell_normal),
            Paragraph(demo_info, cell_normal),
            Paragraph(cond_info, cell_normal),
            Paragraph(risk_info, cell_normal),
            Paragraph(interv_info, cell_normal),
            Paragraph(action_info, cell_normal),
            Paragraph(status_info, cell_normal),
        ])

    pt_table = Table(
        patient_rows,
        colWidths=[36, 95, 75, 115, 80, 135, 125, 60],
        repeatRows=1,
    )
    pt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_bg]),
    ]))
    story.append(pt_table)
    story.append(Spacer(1, 10))

    # Disclaimer footer
    disclaimer_text = (
        "<b>CLINICAL DECISION SUPPORT DISCLAIMER:</b> ReCare AI is a synthetic-data demonstration platform. "
        "Its risk predictions and intervention recommendations are intended solely for care-coordination workflow triage and do not "
        "replace the clinical judgment of licensed physicians, nurses, or pharmacists. No autonomous medical actions or prescriptions are authorized."
    )
    story.append(Paragraph(disclaimer_text, cell_disclaimer))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
