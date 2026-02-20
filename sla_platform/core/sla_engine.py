from django.utils import timezone
from .models import SLAContract, EscalationRule, EscalationLog
from .risk_engine import calculate_risk
from .models import EngineerProfile


def calculate_sla_status(ticket):

    try:
        sla = SLAContract.objects.get(
            client=ticket.client,
            priority=ticket.priority
        )
    except SLAContract.DoesNotExist:
        return "NO_SLA_DEFINED"

    now = timezone.now()

    # Freeze timer if resolved
    end_time = ticket.resolved_at if ticket.resolved_at else now

    total_allowed_seconds = sla.resolution_time_hours * 3600
    used_seconds = (end_time - ticket.created_at).total_seconds()

    usage_percent = (used_seconds / total_allowed_seconds) * 100

    # Risk update
    calculate_risk(ticket, usage_percent)

    # Escalation logic
    rules = EscalationRule.objects.filter(
        priority=ticket.priority,
        threshold_percent__lte=usage_percent
    ).order_by('-threshold_percent')
    if rules.exists():
        highest_rule = rules.first()

        if ticket.current_escalation_level < highest_rule.escalate_to_level:

        # Assign to Team Lead automatically
            engineer_profile = EngineerProfile.objects.filter(
                user=ticket.assigned_to
            ).first()

            if engineer_profile and engineer_profile.team:
                team_lead = EngineerProfile.objects.filter(
                    team=engineer_profile.team,
                    is_team_lead=True
                 ).first()

                if team_lead:
                    ticket.assigned_to = team_lead.user

            ticket.current_escalation_level = highest_rule.escalate_to_level
            ticket.escalation_count += 1

            EscalationLog.objects.create(
                ticket=ticket,
                level=highest_rule.escalate_to_level
            )

    # Breach detection
    if usage_percent >= 100 and ticket.status != "RESOLVED":
        ticket.breached = True
        ticket.breach_time = now
        ticket.status = "BREACHED"

    ticket.save()

    if ticket.status == "RESOLVED":
        return "RESOLVED"

    if usage_percent >= 90:
        return "CRITICAL_RISK"

    if usage_percent >= 70:
        return "WARNING"

    return "ON_TRACK"



def calculate_time_metrics(ticket):
    try:
        sla = SLAContract.objects.get(
            client=ticket.client,
            priority=ticket.priority
        )
    except SLAContract.DoesNotExist:
        return None

    now = timezone.now()
    end_time = ticket.resolved_at if ticket.resolved_at else now

    total_allowed_seconds = sla.resolution_time_hours * 3600
    used_seconds = (end_time - ticket.created_at).total_seconds()

    # 🔥 Handle pause safely
    pause_hours = ticket.total_pause_duration if ticket.total_pause_duration else 0
    used_seconds -= pause_hours * 3600

    # Prevent negative usage
    if used_seconds < 0:
        used_seconds = 0

    remaining_seconds = total_allowed_seconds - used_seconds

    # Prevent negative remaining
    if remaining_seconds < 0:
        remaining_seconds = 0

    usage_percent = 0
    if total_allowed_seconds > 0:
        usage_percent = (used_seconds / total_allowed_seconds) * 100

    return {
        "remaining_hours": round(remaining_seconds / 3600, 2),
        "remaining_minutes": round(remaining_seconds / 60, 2),
        "usage_percent": round(usage_percent, 2),
        "is_breached": remaining_seconds <= 0
    }
