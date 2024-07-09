from django.db import models
from datetime import datetime
from apps.claim_manager.models.claim import Claim
from apps.risk_manager.models.insurance_line import InsuranceLine

class ClaimCredited(models.Model):
    claim = models.ForeignKey(Claim, related_name='crediteds', on_delete=models.SET_NULL, null=True, blank=True)
    insurance_line = models.ForeignKey(InsuranceLine, related_name='crediteds', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(null=True)
    amount = models.FloatField(null=True)
    payment_proof = models.FileField(upload_to='claim_credited/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.claim}, {self.date}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Claims' Credits"
        db_table = 'claims_credited'