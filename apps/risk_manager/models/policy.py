from django.db import models

from apps.client_manager.models.client import Client
from apps.risk_manager.models.risk import Risk

class Policy(models.Model):
    risk = models.ForeignKey(Risk, related_name='policies', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, related_name='policies', on_delete=models.SET_NULL, null=True, blank=True)
    issue_date = models.DateTimeField(null=True)
    renewal_date = models.DateTimeField(null=True)
    number = models.CharField(max_length=255)
    file = models.FileField(upload_to='policies/')
    description = models.TextField(blank=True, null=True)
    net_premium = models.FloatField(null=True)
    commission_type = models.CharField(max_length=255, null=True)
    commission_value = models.FloatField(null=True)

    def __str__(self):
        return f"{self.number}, {self.risk}"

    class Meta:
        ordering = ['-issue_date']
        verbose_name_plural = "       Policies"
        db_table = 'policies'

class PolicyFile(models.Model):
    policy = models.ForeignKey(Policy, related_name='files', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='policy_files/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ['-date']
        verbose_name_plural = "       Policy Files"
        db_table = 'policy_files'