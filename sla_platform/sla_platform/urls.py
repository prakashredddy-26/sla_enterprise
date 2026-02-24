from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from core.views import engineer_register
from core.views import client_dashboard
from core.views import create_ticket
from core.views import update_ticket_status
from core.views import user_login, user_logout
from core.views import governance_metrics
from core.views import system_health
from core.views import backend_status
from core.views import engineer_performance
from core.views import reopen_ticket
from core.views import (
    dashboard,
    governance_dashboard,
    governance_api,
    risk_data_api,
    client_register
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('governance/', governance_dashboard, name='governance_dashboard'),
    path('api/governance/', governance_api, name='governance_api'),
    path('api/risk-data/', risk_data_api, name='risk_data_api'),
    path('client/register/', client_register, name='client_register'),
    path('engineer/register/', engineer_register, name='engineer_register'),
    path('client/dashboard/', client_dashboard, name='client_dashboard'),
    path('client/create-ticket/', create_ticket, name='create_ticket'),
    path('engineer/update-ticket/<int:ticket_id>/', update_ticket_status, name='update_ticket_status'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('api/governance-metrics/', governance_metrics, name='governance_metrics'),
    path('api/engineer-performance/', engineer_performance, name='engineer_performance'),
    path('api/system-health/', system_health, name='system_health'),
    path('api/backend-status/', backend_status, name='backend_status'),
    path("ticket/reopen/<int:ticket_id>/", reopen_ticket, name="reopen_ticket"),

    # ✅ Change Password (Profile menu)
    path("password-change/", auth_views.PasswordChangeView.as_view(
        template_name="registration/password_change_form.html"
    ), name="password_change"),

    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="registration/password_change_done.html"
    ), name="password_change_done"),
]