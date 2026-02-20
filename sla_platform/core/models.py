from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ---------------- SOFT DELETE MANAGER ---------------- #

class ActiveTicketManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


# ---------------- CORE MODELS ---------------- #

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class EngineerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    is_team_lead = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.team.name if self.team else 'No Team'}"


class SLAContract(models.Model):
    PRIORITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    resolution_time_hours = models.IntegerField()

    class Meta:
        unique_together = ("client", "priority")

    def __str__(self):
        return f"{self.client.name} - {self.priority}"


# ---------------- TICKET MODEL ---------------- #

class Ticket(models.Model):

    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('REOPENED', 'Reopened'),
        ('BREACHED', 'Breached'),
    ]

    PRIORITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    CATEGORY_CHOICES = [
        ('NETWORK', 'Network Operations'),
        ('CLOUD', 'Cloud Infrastructure'),
        ('SERVER', 'Server Administration'),
        ('DATABASE', 'Database Administration'),
        ('DEVOPS', 'DevOps'),
        ('CYBER', 'Cybersecurity'),
        ('RISK', 'Risk & Compliance'),
        ('APP', 'Application Support'),
        ('AI', 'AI/ML Operations'),
        ('DATA', 'Data Engineering'),
        ('SRE', 'SRE'),
        ('INCIDENT', 'Incident Response'),
    ]

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    current_escalation_level = models.IntegerField(default=0)
    escalation_count = models.IntegerField(default=0)
    breached = models.BooleanField(default=False)
    breach_time = models.DateTimeField(null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    risk_level = models.CharField(max_length=20, null=True, blank=True)
    sla_deadline = models.DateTimeField(null=True, blank=True)

    sla_paused = models.BooleanField(default=False)
    pause_started_at = models.DateTimeField(null=True, blank=True)
    total_pause_duration = models.FloatField(default=0)

    # Managers
    objects = ActiveTicketManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def save(self, *args, **kwargs):

        # Set SLA deadline
        if not self.sla_deadline and self.created_at:
            try:
                sla = SLAContract.objects.get(
                    client=self.client,
                    priority=self.priority
                )
                self.sla_deadline = self.created_at + timezone.timedelta(
                    hours=sla.resolution_time_hours
                )
            except SLAContract.DoesNotExist:
                pass

        # Auto set resolved_at
        if self.status == "RESOLVED" and not self.resolved_at:
            self.resolved_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket #{self.id}"
        

# ---------------- OTHER MODELS ---------------- #

class EscalationRule(models.Model):
    priority = models.CharField(max_length=20)
    threshold_percent = models.IntegerField()
    escalate_to_level = models.IntegerField()

    def __str__(self):
        return f"{self.priority} - {self.threshold_percent}%"


class EscalationLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    escalated_at = models.DateTimeField(auto_now_add=True)
    level = models.IntegerField()


class TicketAuditLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_at = models.DateTimeField(auto_now_add=True)


class TicketAudit(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)