from .schemas import LeadProfile


SAMPLE_LEADS = [
    LeadProfile(
        id="lead-001",
        full_name="Rhea Mehta",
        local_hour=11,
        phone="+1-415-555-0101",
        city="San Jose",
        state="CA",
        interest="water purifier subscription",
        budget_band="mid",
        consent_status="unknown",
        do_not_call=False,
        persona="Busy parent who values time, health, and straightforward offers.",
        notes="Mentioned apartment move on web form three weeks ago.",
    ),
    LeadProfile(
        id="lead-002",
        full_name="Marcus Hill",
        local_hour=19,
        phone="+1-206-555-0132",
        city="Tacoma",
        state="WA",
        interest="home solar consultation",
        budget_band="high",
        consent_status="consented",
        do_not_call=False,
        persona="Research-heavy buyer who asks ROI questions and dislikes pushy sales.",
        notes="Downloaded ROI guide and clicked financing FAQ.",
    ),
    LeadProfile(
        id="lead-003",
        full_name="Anita Rao",
        local_hour=21,
        phone="+1-512-555-0177",
        city="Austin",
        state="TX",
        interest="kitchen renovation estimate",
        budget_band="premium",
        consent_status="revoked",
        do_not_call=True,
        persona="Previously interested but explicitly opted out after a pricing call.",
        notes="Must remain blocked due to DNC + revoked consent.",
    ),
]


def get_lead(lead_id: str) -> LeadProfile:
    for lead in SAMPLE_LEADS:
        if lead.id == lead_id:
            return lead
    raise KeyError(f"Unknown lead_id: {lead_id}")
