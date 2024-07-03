from django.db import models

from apps.risk_manager.models.insurance_line import InsuranceLine

class PremiumDebited(models.Model):
    insurance_line = models.ForeignKey(InsuranceLine, related_name='debiteds', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(null=True)
    amount = models.FloatField(null=True)
    payment_proof = models.FileField(upload_to='premium_debited/', null=True, blank=True)

    def __str__(self):
        return f"{self.insurance_line}, {self.amount}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Premiums Debited"
        db_table = 'premiums_debited'