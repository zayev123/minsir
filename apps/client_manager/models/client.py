from django.db import models

from apps.account_manager.models.user import User
from apps.agent_manager.models.agent import Agent

class Client(models.Model):
    agent = models.ForeignKey(Agent, related_name='clients', on_delete=models.SET_NULL, null=True)
    user = models.OneToOneField(User, related_name='client', on_delete=models.CASCADE, blank=True, null=True)
    address_area = models.TextField()
    industry = models.CharField(max_length=255)
    relation = models.CharField(max_length=255)
    connected_through = models.CharField(max_length=255)
    follow_up_frequency_days = models.IntegerField()
    notes = models.TextField()

    def __str__(self):
        return self.user
    
    class Meta:
        # ordering = ['-status_changed_at']
        verbose_name_plural = "       Clients"
        db_table = 'clients'