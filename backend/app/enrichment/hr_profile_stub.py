from __future__ import annotations

from typing import Any, Dict, Optional

# Simulated HR profile data keyed by Engineer_ID.
# In production this would be a read-only HRIS connector (Workday / SAP SuccessFactors).
# Each profile follows the NormalizedActivityRecord HR context contract.
_HR_PROFILES: Dict[str, Dict[str, Any]] = {
    "ENG-00387": {
        "hr_job_title": "Senior Network Systems Engineer",
        "hr_job_family": "Network Engineering",
        "hr_job_code": "NE-SR-04",
        "hr_org_unit": "System Performance",
        "hr_department": "Core Network Operations",
        "hr_cost_centre": "CC-NET-1042",
        "hr_seniority": "Senior",
        "hr_employee_type": "FTE",
        "hr_location": "Basking Ridge, NJ",
        "hr_persona": "Network Engineering Annual Survey",
    },
    "ENG-00819": {
        "hr_job_title": "Network Planning Engineer II",
        "hr_job_family": "Network Engineering",
        "hr_job_code": "NE-P2-03",
        "hr_org_unit": "Network Planning",
        "hr_department": "Capital Network Expansion",
        "hr_cost_centre": "CC-NET-2011",
        "hr_seniority": "Mid-level",
        "hr_employee_type": "FTE",
        "hr_location": "Irving, TX",
        "hr_persona": "Network Engineering Annual Survey",
    },
    "ENG-00922": {
        "hr_job_title": "Systems Performance Analyst",
        "hr_job_family": "Network Engineering",
        "hr_job_code": "NE-PA-02",
        "hr_org_unit": "System Performance",
        "hr_department": "Core Network Operations",
        "hr_cost_centre": "CC-NET-1042",
        "hr_seniority": "Mid-level",
        "hr_employee_type": "FTE",
        "hr_location": "Tampa, FL",
        "hr_persona": "Network Engineering Annual Survey",
    },
    "ENG-01103": {
        "hr_job_title": "Field Network Construction Lead",
        "hr_job_family": "Field Engineering",
        "hr_job_code": "FE-CL-05",
        "hr_org_unit": "Field Operations",
        "hr_department": "Fiber Deployment",
        "hr_cost_centre": "CC-FLD-3301",
        "hr_seniority": "Lead",
        "hr_employee_type": "FTE",
        "hr_location": "Atlanta, GA",
        "hr_persona": "Network Deployment Survey",
    },
    "ENG-01452": {
        "hr_job_title": "Network Planning Engineer III",
        "hr_job_family": "Network Engineering",
        "hr_job_code": "NE-P3-04",
        "hr_org_unit": "Network Planning",
        "hr_department": "Capital Network Expansion",
        "hr_cost_centre": "CC-NET-2011",
        "hr_seniority": "Senior",
        "hr_employee_type": "FTE",
        "hr_location": "Dallas, TX",
        "hr_persona": "Network Engineering Annual Survey",
    },
    "ENG-00631": {
        "hr_job_title": "Network Assurance Engineer",
        "hr_job_family": "Network Assurance",
        "hr_job_code": "NA-AE-03",
        "hr_org_unit": "Network Assurance",
        "hr_department": "Network Quality & Reliability",
        "hr_cost_centre": "CC-NQR-4105",
        "hr_seniority": "Mid-level",
        "hr_employee_type": "FTE",
        "hr_location": "Alpharetta, GA",
        "hr_persona": "Network Engineering Annual Survey",
    },
    "ENG-01821": {
        "hr_job_title": "Principal Systems Engineer",
        "hr_job_family": "Network Engineering",
        "hr_job_code": "NE-PR-06",
        "hr_org_unit": "System Performance",
        "hr_department": "Core Network Operations",
        "hr_cost_centre": "CC-NET-1042",
        "hr_seniority": "Principal",
        "hr_employee_type": "FTE",
        "hr_location": "Basking Ridge, NJ",
        "hr_persona": "Network Engineering Annual Survey",
    },
    "ENG-01794": {
        "hr_job_title": "Network Systems Engineer II",
        "hr_job_family": "Network Engineering",
        "hr_job_code": "NE-SE-03",
        "hr_org_unit": "System Performance",
        "hr_department": "Core Network Operations",
        "hr_cost_centre": "CC-NET-1042",
        "hr_seniority": "Mid-level",
        "hr_employee_type": "FTE",
        "hr_location": "Irvine, CA",
        "hr_persona": "Network Engineering Annual Survey",
    },
}

_STUB_PROFILE: Dict[str, Any] = {
    "hr_job_title": None,
    "hr_job_family": None,
    "hr_job_code": None,
    "hr_org_unit": None,
    "hr_department": None,
    "hr_cost_centre": None,
    "hr_seniority": None,
    "hr_employee_type": "FTE",
    "hr_location": None,
    "hr_persona": None,
    "_hrProfileSource": "stub-not-found",
}


def get_hr_profile(engineer_id: Optional[str]) -> Dict[str, Any]:
    """Returns the simulated HR profile for an engineer.

    Production replacement: HRIS connector (Workday / SAP SuccessFactors)
    keyed by employee ID with read-only scoped access.
    """
    if not engineer_id:
        return {**_STUB_PROFILE, "_hrProfileSource": "stub-missing-id"}
    profile = _HR_PROFILES.get(str(engineer_id).strip())
    if profile:
        return {**profile, "_hrProfileSource": "stub-matched"}
    return {**_STUB_PROFILE, "_hrProfileSource": f"stub-not-found:{engineer_id}"}
