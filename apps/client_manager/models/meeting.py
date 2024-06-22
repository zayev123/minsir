from django.db import models

from apps.account_manager.models.insurance_company import InsuranceCompany
from apps.client_manager.models.client import Client
from apps.risk_manager.models.risk import Risk

class Meeting(models.Model):
    client = models.ForeignKey(Client, related_name='meetings', on_delete=models.SET_NULL, null=True, blank=True)
    insurance_company = models.ForeignKey(InsuranceCompany, related_name='meetings', on_delete=models.SET_NULL, null=True, blank=True)
    risk = models.ForeignKey(Risk, related_name='meetings', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    type = models.CharField(max_length=255)
    mode = models.CharField(max_length=255)
    primary_issue_type = models.CharField(max_length=255)
    main_points = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"{self.risk}, {self.primary_issue_type}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Meetings"
        db_table = 'meetings'