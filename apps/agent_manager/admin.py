from django.contrib import admin

from apps.agent_manager.models.agent import Agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type',]
    search_fields = ['id', 'user__name', 'type',]