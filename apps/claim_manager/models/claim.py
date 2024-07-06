from django.db import models

from apps.client_manager.models.client import Client
from apps.risk_manager.models.policy import Policy

class Claim(models.Model):
    policy = models.ForeignKey(Policy, related_name='claims', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, related_name='claims', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Client, related_name='company_claims', on_delete=models.SET_NULL, null=True, blank=True)
    number = models.CharField(max_length=255, null=True)
    date_of_intimation = models.DateTimeField(null=True)
    date_of_occurrence = models.DateTimeField(null=True)
    description = models.TextField(blank=True, null=True)
    cash_call_amount = models.FloatField(null=True)
    settlement_amount = models.FloatField(null=True)

    def __str__(self):
        return f"{self.policy}, {self.date_of_intimation}"

    class Meta:
        ordering = ['-date_of_intimation']
        verbose_name_plural = "       Claims"
        db_table = 'claims'