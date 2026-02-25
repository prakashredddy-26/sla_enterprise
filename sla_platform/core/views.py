from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone

from django.db.models import Count, Q

from .models import (
    Ticket,
    Client,
    Department,
    EngineerProfile,
    Team,
    SLAContract,
    Notification,
    TicketAuditLog,
    TicketAudit
)

from .sla_engine import calculate_sla_status, calculate_time_metrics
from .governance_engine import (
    calculate_sla_health,
    calculate_breach_rate,
    calculate_total_escalations,
    calculate_average_resolution_time
)

# ---------------- ROLE CHECK FUNCTIONS ---------------- #

def is_admin(user):
    return user.groups.filter(name='ADMIN').exists() or user.is_superuser

def is_engineer(user):
    return user.groups.filter(name='ENGINEERS').exists()

def is_client(user):
    return hasattr(user, 'client')


# ---------------- CLIENT REGISTER ---------------- #

def client_register(request):
    success_message = None
    if request.method == "POST":
        print("REGISTER FUNCTION CALLED")

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists.")

        print("Creating user...")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        group, created = Group.objects.get_or_create(name='CLIENTS')
        user.groups.add(group)

        print("Creating client profile...")

        Client.objects.create(
            user=user,
            name=username,
            email=email
        )

        print("Client profile created")

        success_message = "Client Registered Successfully! You can now login."

    return render(request, "client_register.html", {"success_message": success_message})


# ---------------- ENGINEER REGISTER ---------------- #

def engineer_register(request):
    success_message = None
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists.")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.is_staff = True
        user.save()

        group, created = Group.objects.get_or_create(name='ENGINEERS')
        user.groups.add(group)

        success_message = "Engineer Registered Successfully! You can now login."

    return render(request, "engineer_register.html", {"success_message": success_message})


# ---------------- MAIN DASHBOARD ---------------- #

@login_required
def dashboard(request):
    user = request.user

    # ✅ Choose tickets by role
    if is_engineer(user):
        base_qs = Ticket.objects.filter(assigned_to=user)
    elif is_client(user):
        base_qs = Ticket.objects.filter(client=user.client)
    else:
        base_qs = Ticket.objects.all()

    # ✅ KPI counts computed in BACKEND (no JS dependency)
    total_tickets = base_qs.count()
    breached_count = base_qs.filter(breached=True).count()
    resolved_count = base_qs.filter(status="RESOLVED").count()
    active_count = base_qs.filter(status__in=["NEW", "IN_PROGRESS", "REOPENED"]).count()

    # ✅ Build dashboard rows (your existing structure)
    dashboard_data = []
    for ticket in base_qs:
        metrics = calculate_time_metrics(ticket)
        sla_status = calculate_sla_status(ticket)

        dashboard_data.append({
            "ticket": ticket,
            "sla_status": sla_status,
            "remaining_hours": metrics["remaining_hours"] if metrics else None,
            "usage_percent": metrics["usage_percent"] if metrics else None,
        })

    notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).order_by("-created_at")

    return render(request, "dashboard.html", {
        "tickets": dashboard_data,
        "notifications": notifications,
        "is_engineer": is_engineer(user),
        "is_client": is_client(user),

        # ✅ KPIs for template
        "total_tickets": total_tickets,
        "breached_count": breached_count,
        "resolved_count": resolved_count,
        "active_count": active_count,
    })


# ---------------- CLIENT DASHBOARD ---------------- #

@login_required
def client_dashboard(request):
    if not is_client(request.user):
        return redirect('dashboard')

    try:
        client = request.user.client
    except:
        return HttpResponse("Client profile not found.")

    tickets = Ticket.objects.filter(client=client)

    total_tickets = tickets.count()
    breached_count = tickets.filter(breached=True).count()

    open_tickets = tickets.filter(status__in=["NEW", "IN_PROGRESS", "REOPENED"]).count()

    sla_met = tickets.filter(status="RESOLVED", breached=False).count()

    return render(request, "client_dashboard.html", {
        "tickets": tickets,
        "total_tickets": total_tickets,
        "breached_count": breached_count,
        "open_tickets": open_tickets,
        "sla_met": sla_met,
    })


# ---------------- GOVERNANCE DASHBOARD ---------------- #

@login_required
def governance_dashboard(request):
    if not is_admin(request.user):
        return redirect('dashboard')

    context = {
        "sla_health": calculate_sla_health(),
        "breach_rate": calculate_breach_rate(),
        "total_escalations": calculate_total_escalations(),
        "avg_resolution_time": calculate_average_resolution_time(),
    }

    return render(request, "governance_dashboard.html", context)


# ---------------- GOVERNANCE API ---------------- #

@login_required
def governance_api(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    data = {
        "sla_health": calculate_sla_health(),
        "breach_rate": calculate_breach_rate(),
        "total_escalations": calculate_total_escalations(),
        "avg_resolution_time": calculate_average_resolution_time(),
    }

    return JsonResponse(data)


# ---------------- RISK DATA API ---------------- #

@login_required
def risk_data_api(request):

    if is_client(request.user):
        tickets = Ticket.objects.filter(client=request.user.client)

    elif is_engineer(request.user):
        tickets = Ticket.objects.filter(assigned_to=request.user)

    elif is_admin(request.user):
        tickets = Ticket.objects.all()

    else:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    data = []

    for ticket in tickets:
        data.append({
            "ticket_id": ticket.id,
            "risk_score": ticket.risk_score,
            "risk_level": ticket.risk_level,
            "priority": ticket.priority,
        })

    return JsonResponse({"tickets": data})


# 🔥 Category → Department mapping
CATEGORY_DEPT_MAP = {
    'NETWORK': 'Network Operations',
    'CLOUD': 'Cloud Infrastructure',
    'SERVER': 'Server Administration',
    'DATABASE': 'Database Administration',
    'DEVOPS': 'DevOps',
    'CYBER': 'Cybersecurity',
    'RISK': 'Risk & Compliance',
    'APP': 'Application Support',
    'AI': 'AI/ML Operations',
    'DATA': 'Data Engineering',
    'SRE': 'SRE (Site Reliability Engineering)',
    'INCIDENT': 'Incident Response Team',
}


@login_required
def create_ticket(request):

    if not is_client(request.user):
        return HttpResponse("Only clients can create tickets.")

    try:
        client = request.user.client
    except:
        return HttpResponse("Client profile not found.")

    if request.method == "POST":

        description = request.POST.get("description")
        priority = request.POST.get("priority")
        category = request.POST.get("category")

        department_name = CATEGORY_DEPT_MAP.get(category)

        if not department_name:
            return HttpResponse("Invalid category selected.")

        try:
            department = Department.objects.get(name=department_name)
        except Department.DoesNotExist:
            return HttpResponse("Department not configured in admin.")

        try:
            sla = SLAContract.objects.get(
                client=client,
                priority=priority
            )
        except SLAContract.DoesNotExist:
            sla = None

        engineers = EngineerProfile.objects.filter(
            team__department=department
        ).select_related("user")

        if not engineers.exists():
            return HttpResponse("No engineers available in this department.")

        least_loaded_engineer = None
        least_ticket_count = None

        for engineer in engineers:

            active_count = Ticket.objects.filter(
                assigned_to=engineer.user,
                status__in=["NEW", "IN_PROGRESS", "REOPENED"]
            ).count()

            if active_count >= 5:
                continue

            if least_ticket_count is None or active_count < least_ticket_count:
                least_ticket_count = active_count
                least_loaded_engineer = engineer.user

        if least_loaded_engineer is None:
            return HttpResponse("All engineers currently overloaded.")

        ticket = Ticket.objects.create(
            client=client,
            description=description,
            priority=priority,
            category=category,
            department=department,
            assigned_to=least_loaded_engineer,
            status="NEW"
        )

        Notification.objects.create(
            user=least_loaded_engineer,
            ticket=ticket,
            message=f"You have been assigned Ticket #{ticket.id}"
        )

        if least_loaded_engineer.email:
            send_mail(
                subject="New SLA Ticket Assigned",
                message=f"You have been assigned Ticket #{ticket.id}",
                from_email="noreply@sla-enterprise.com",
                recipient_list=[least_loaded_engineer.email],
                fail_silently=True
            )

        return redirect("client_dashboard")

    return render(request, "create_ticket.html")


# ---------------- AUTH ---------------- #

def user_login(request):
    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if next_url:
                return redirect(next_url)

            return redirect("dashboard")

        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, "login.html", {"next": next_url})

    return render(request, "login.html", {"next": next_url})


def user_logout(request):
    logout(request)
    return redirect("login")


# ---------------- ENGINEER UPDATE TICKET ---------------- #

@login_required
def update_ticket_status(request, ticket_id):

    if not is_engineer(request.user):
        return HttpResponse("Only engineers can update tickets.")

    try:
        ticket = Ticket.objects.get(id=ticket_id, assigned_to=request.user)
    except Ticket.DoesNotExist:
        return HttpResponse("Ticket not found or not assigned to you.")

    if request.method == "POST":
        new_status = request.POST.get("status")
        old_status = ticket.status
        ticket.status = new_status
        ticket.save()

        TicketAuditLog.objects.create(
            ticket=ticket,
            changed_by=request.user,
            old_status=old_status,
            new_status=ticket.status
        )

        TicketAudit.objects.create(
            ticket=ticket,
            action=f"Status changed to {new_status}",
            performed_by=request.user
        )

        return redirect('dashboard')

    return render(request, "update_ticket.html", {"ticket": ticket})


# ---------------- GOVERNANCE METRICS API ---------------- #

@login_required
def governance_metrics(request):

    total = Ticket.objects.count()
    breached = Ticket.objects.filter(breached=True).count()
    resolved = Ticket.objects.filter(status="RESOLVED").count()
    in_progress = Ticket.objects.filter(status="IN_PROGRESS").count()

    data = {
        "total_tickets": total,
        "breached": breached,
        "resolved": resolved,
        "in_progress": in_progress,
        "sla_health_score": round((resolved / total) * 100, 2) if total else 100
    }

    return JsonResponse(data)


@login_required
def engineer_performance(request):

    engineers = EngineerProfile.objects.all()
    performance_data = []

    for engineer in engineers:

        total = Ticket.objects.filter(assigned_to=engineer.user).count()
        resolved = Ticket.objects.filter(
            assigned_to=engineer.user,
            status="RESOLVED"
        ).count()

        breached = Ticket.objects.filter(
            assigned_to=engineer.user,
            breached=True
        ).count()

        performance_data.append({
            "engineer": engineer.user.username,
            "total": total,
            "resolved": resolved,
            "breached": breached,
        })

    return JsonResponse(performance_data, safe=False)


@login_required
def system_health(request):

    total = Ticket.objects.count()
    breached = Ticket.objects.filter(breached=True).count()

    if total == 0:
        health = 100
    else:
        health = round(((total - breached) / total) * 100, 2)

    risk_high = Ticket.objects.filter(risk_level="HIGH").count()

    return JsonResponse({
        "system_sla_health": health,
        "total_tickets": total,
        "breached": breached,
        "high_risk_tickets": risk_high
    })


@login_required
def backend_status(request):

    return JsonResponse({
        "load_balancing": True,
        "sla_engine": True,
        "escalation": True,
        "audit_trail": True,
        "risk_engine": True,
        "team_hierarchy": True,
        "governance_metrics": True,
        "engineer_performance": True
    })


# ---------------- CLIENT REOPEN TICKET ---------------- #

@login_required
def reopen_ticket(request, ticket_id):

    if not hasattr(request.user, "client"):
        return HttpResponse("Only client can reopen ticket.")

    ticket = get_object_or_404(
        Ticket,
        id=ticket_id,
        client=request.user.client
    )

    if ticket.status != "RESOLVED":
        return HttpResponse("Only resolved tickets can be reopened.")

    ticket.status = "REOPENED"
    ticket.resolved_at = None
    ticket.save()

    Notification.objects.create(
        user=ticket.assigned_to,
        ticket=ticket,
        message=f"Ticket #{ticket.id} has been reopened."
    )

    return redirect("client_dashboard")


# ---------------- CLIENT DELETE TICKET (SOFT DELETE) ---------------- #

@login_required
def delete_ticket(request, ticket_id):

    if not hasattr(request.user, "client"):
        return HttpResponse("Only clients can delete tickets.")

    ticket = get_object_or_404(
        Ticket,
        id=ticket_id,
        client=request.user.client
    )

    ticket.soft_delete()

    Notification.objects.create(
        user=ticket.assigned_to,
        ticket=ticket,
        message=f"Ticket #{ticket.id} was deleted by client."
    )

    return redirect("client_dashboard")