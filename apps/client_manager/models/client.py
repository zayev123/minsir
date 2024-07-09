from django.db import models
from datetime import datetime
from apps.account_manager.models.user import User
from apps.agent_manager.models.agent import Agent

class Client(models.Model):
    agent = models.ForeignKey(Agent, related_name='clients', on_delete=models.SET_NULL, blank=True, null=True)
    user = models.OneToOneField(User, related_name='client', on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    address_area = models.TextField()
    industry = models.CharField(max_length=255, blank=True, null=True)
    relation = models.CharField(max_length=255, blank=True, null=True)
    connected_through = models.CharField(max_length=255, blank=True, null=True)
    follow_up_frequency_days = models.IntegerField(null=True)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.name
    
    class Meta:
        # ordering = ['-status_changed_at']
        verbose_name_plural = "       Clients"
        db_table = 'clients'