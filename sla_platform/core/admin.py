from django.contrib import admin
from .models import (
    Client,
    Department,
    Team,
    EngineerProfile,
    SLAContract,
    Ticket,
    EscalationRule,
    EscalationLog
)

admin.site.site_header = "SLA Enterprise Control Panel"
admin.site.site_title = "SLA Enterprise"
admin.site.index_title = "SLA Governance Dashboard"
# Engineer Inline (Hierarchy View)

class EngineerInline(admin.TabularInline):
    model = EngineerProfile
    extra = 0
    fields = ('user', 'is_team_lead')
    show_change_link = True


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    inlines = [EngineerInline]

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)

# @admin.register(EngineerProfile)
# class EngineerProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'team', 'is_team_lead')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user')



@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client',
        'category',
        'department',
        'priority',
        'assigned_to',
        'status',
        'created_at'
    )
    list_filter = ('status', 'priority', 'category', 'department')



# Simple Registrations
admin.site.register(SLAContract)
admin.site.register(EscalationRule)
admin.site.register(EscalationLog)
