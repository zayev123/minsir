from django.db import models

from apps.risk_manager.models.policy import Policy

class Claim(models.Model):
    policy = models.ForeignKey(Policy, related_name='claims', on_delete=models.SET_NULL, null=True, blank=True)
    number = models.CharField(max_length=255)
    date_of_intimation = models.DateTimeField()
    date_of_occurrence = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    cash_call_amount = models.FloatField()
    settlement_amount = models.FloatField()

    def __str__(self):
        return f"{self.policy}, {self.date_of_intimation}"

    class Meta:
        ordering = ['-date_of_intimation']
        verbose_name_plural = "       Claims"
        db_table = 'claims'