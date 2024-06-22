from django.db import models

from apps.risk_manager.models.policy import Policy

class PremiumCredited(models.Model):
    policy = models.ForeignKey(Policy, related_name='crediteds', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    amount = models.FloatField()
    payment_proof = models.FileField(upload_to='premium_credited/')

    def __str__(self):
        return f"{self.policy}, {self.amount}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Premiums Credited"
        db_table = 'premiums_credited'