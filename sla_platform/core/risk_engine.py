from .models import Ticket


PRIORITY_WEIGHTS = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def calculate_risk(ticket, usage_percent):
    priority_weight = PRIORITY_WEIGHTS.get(ticket.priority, 1)

    risk_score = (
        (usage_percent * 0.6)
        + (priority_weight * 10)
        + (ticket.escalation_count * 5)
    )

    risk_score = min(risk_score, 100)

    if risk_score <= 40:
        risk_level = "LOW"
    elif risk_score <= 70:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    ticket.risk_score = round(risk_score, 2)
    ticket.risk_level = risk_level
    ticket.save()

    return risk_score, risk_level
