from django.db import models

from apps.claim_manager.models.claim import Claim
from apps.client_manager.models.client import Client

class ClaimDebited(models.Model):
    claim = models.ForeignKey(Claim, related_name='debiteds', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, related_name='claims_debited', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(null=True)
    amount = models.FloatField(null=True)
    payment_proof = models.FileField(upload_to='claim_debited/', null=True, blank=True)

    def __str__(self):
        return f"{self.claim}, {self.date}"
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Claims' Debits"
        db_table = 'claims_debited'


class ClaimDebitedFile(models.Model):
    claim_debited = models.ForeignKey(ClaimDebited, related_name='files', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='claims_debited_files/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ['-date']
        verbose_name_plural = "       Claim Debited Files"
        db_table = 'claims_debited_files'