from django.db import models

from apps.account_manager.models.insurance_company import InsuranceCompany
from apps.risk_manager.models.policy import Policy

class InsuranceLine(models.Model):
    insurance_company = models.ForeignKey(InsuranceCompany, related_name='lines', on_delete=models.SET_NULL, null=True, blank=True)
    policy = models.ForeignKey(Policy, related_name='lines', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    policy_number = models.CharField(max_length=255)
    line_written = models.FloatField()
    share_percentage = models.FloatField()
    notes = models.TextField(blank=True, null=True)
    net_premium = models.FloatField()

    def __str__(self):
        return f"{self.policy}, {self.line_written}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Insurance Lines"
        db_table = 'insurance_lines'