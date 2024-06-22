from django.db import models

from apps.claim_manager.models.claim import Claim

class ClaimDebited(models.Model):
    claim = models.ForeignKey(Claim, related_name='debiteds', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    amount = models.FloatField()
    payment_proof = models.FileField(upload_to='claim_debited/')

    def __str__(self):
        return f"{self.claim}, {self.date}"
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Claims' Debits"
        db_table = 'claims_debited'