from django.utils import timezone
from django.db.models import Avg, Count
from .models import Ticket, EngineerProfile
from .models import Team

def calculate_sla_health():

    total = Ticket.objects.count()

    if total == 0:
        return 100

    resolved = Ticket.objects.filter(status="RESOLVED").count()

    breached = Ticket.objects.filter(breached=True).count()

    healthy = resolved - breached

    return round((healthy / total) * 100, 2)



def calculate_breach_rate():
    total_tickets = Ticket.objects.count()
    breached_tickets = Ticket.objects.filter(breached=True).count()

    if total_tickets == 0:
        return 0

    return round((breached_tickets / total_tickets) * 100, 2)


def calculate_total_escalations():
    return Ticket.objects.aggregate(
        total_escalations=Avg("escalation_count")
    )["total_escalations"] or 0


def calculate_average_resolution_time():
    resolved_tickets = Ticket.objects.filter(
        resolved_at__isnull=False
    )

    total_hours = 0
    count = resolved_tickets.count()

    if count == 0:
        return 0

    for ticket in resolved_tickets:
        duration = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
        total_hours += duration

    return round(total_hours / count, 2)


def engineer_performance():

    data = []

    engineers = EngineerProfile.objects.all()

    for engineer in engineers:

        resolved_tickets = Ticket.objects.filter(
            assigned_to=engineer.user,
            status="RESOLVED"
        )

        total_resolved = resolved_tickets.count()

        breached = resolved_tickets.filter(breached=True).count()

        success_rate = 0
        if total_resolved > 0:
            success_rate = round(((total_resolved - breached) / total_resolved) * 100, 2)

        data.append({
            "engineer": engineer.user.username,
            "resolved": total_resolved,
            "breached": breached,
            "success_rate": success_rate
        })

    return data

def team_load():

    result = []

    for team in Team.objects.all():

        active_tickets = Ticket.objects.filter(
            department=team.department,
            status__in=["NEW", "IN_PROGRESS"]
        ).count()

        result.append({
            "team": team.name,
            "active_tickets": active_tickets
        })

    return result
