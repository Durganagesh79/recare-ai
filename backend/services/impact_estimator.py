"""
ReCare AI - Impact Estimation & Sensitivity Analysis Engine
Computes illustrative estimates of readmissions averted under explicit reach,
efficacy, and cost assumptions with honest uncertainty boundaries.
"""

from typing import Dict, Any, List


def calculate_impact_scenarios(
    selected_patients_count: int = 50,
    average_readmission_risk: float = 0.42,
    cost_per_readmission: float = 15200.0,  # Average CMS benchmark readmission cost
    cost_per_contact: float = 125.0,        # Transition nurse/pharmacist call allocation
) -> Dict[str, Any]:
    """
    Generate Conservative, Central, and Optimistic readmissions averted impact models.
    """
    # Expected readmissions among selected cohort without any outreach
    expected_readmissions_baseline = selected_patients_count * average_readmission_risk

    scenarios = {
        "conservative": {
            "name": "Conservative Scenario",
            "reach_rate": 0.60,                 # 60% successfully contacted
            "relative_risk_reduction": 0.15,    # 15% RRR from literature lower bound
            "description": "Lower patient contact rate (60%) and minimal intervention adherence (15% RRR).",
        },
        "central": {
            "name": "Central Scenario (Baseline)",
            "reach_rate": 0.75,                 # 75% reach rate
            "relative_risk_reduction": 0.25,    # 25% RRR typical for multifaceted transition care
            "description": "Realistic hospital transition care benchmarks (75% reach, 25% RRR).",
        },
        "optimistic": {
            "name": "Optimistic Scenario",
            "reach_rate": 0.85,                 # 85% reach rate
            "relative_risk_reduction": 0.35,    # 35% RRR high-touch nurse + pharmacist care
            "description": "High engagement rate (85%) with complete multi-disciplinary follow-up.",
        },
    }

    results = {}
    for key, sc in scenarios.items():
        reached = selected_patients_count * sc["reach_rate"]
        baseline_readmissions_in_reached = reached * average_readmission_risk
        averted = baseline_readmissions_in_reached * sc["relative_risk_reduction"]

        gross_savings = averted * cost_per_readmission
        program_cost = selected_patients_count * cost_per_contact
        net_savings = gross_savings - program_cost
        roi_ratio = (gross_savings / program_cost) if program_cost > 0 else 0.0

        results[key] = {
            "scenario_name": sc["name"],
            "reach_rate_pct": round(sc["reach_rate"] * 100, 1),
            "rrr_pct": round(sc["relative_risk_reduction"] * 100, 1),
            "patients_reached": round(reached, 1),
            "estimated_readmissions_averted": round(averted, 1),
            "gross_savings_estimated": round(gross_savings, 2),
            "estimated_program_cost": round(program_cost, 2),
            "net_cost_avoidance": round(net_savings, 2),
            "estimated_roi": round(roi_ratio, 2),
            "description": sc["description"],
        }

    # Sensitivity matrix over grid of reach rates and RRRs
    reach_grid = [0.50, 0.65, 0.75, 0.85, 0.95]
    rrr_grid = [0.10, 0.20, 0.25, 0.30, 0.40]
    sensitivity_grid = []

    for r in reach_grid:
        row = {"reach_rate": int(r * 100)}
        for eff in rrr_grid:
            averted = selected_patients_count * r * average_readmission_risk * eff
            row[f"rrr_{int(eff*100)}"] = round(averted, 2)
        sensitivity_grid.append(row)

    return {
        "cohort_size": selected_patients_count,
        "average_cohort_risk": round(average_readmission_risk, 4),
        "expected_readmissions_unmitigated": round(expected_readmissions_baseline, 1),
        "cost_per_readmission_benchmark": cost_per_readmission,
        "cost_per_contact_benchmark": cost_per_contact,
        "scenarios": results,
        "sensitivity_matrix": sensitivity_grid,
        "uncertainty_disclaimer": (
            "DISCLAIMER: These estimates are illustrative mathematical scenario models based on published health services research "
            "(e.g., Project RED, BOOST, Coleman Care Transitions). They do not represent observed clinical trial results. "
            "Observational risk predictions do not prove causality, and actual readmissions averted require prospective evaluation."
        ),
    }
