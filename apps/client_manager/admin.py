from django.contrib import admin

from apps.client_manager.models.client import Client
from apps.client_manager.models.client_document import ClientDocument
from apps.client_manager.models.client_status import ClientStatus
from apps.client_manager.models.meeting import Meeting

@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'client']
    search_fields = ['id', 'name']

@admin.register(ClientStatus)
class ClientStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'current_status', 'client', 'status_changed_at']
    search_fields = ['id', 'current_status', 'status_changed_at']

@admin.register(Client)
class ClientModelAdmin(admin.ModelAdmin):
    list_display = ['id', "name", 'user', 'industry']
    search_fields = ['id', "name", 'user__name', 'industry']

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'risk', 'primary_issue_type']
    search_fields = ['id', 'primary_issue_type']
