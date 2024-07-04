from django.db import models

from apps.client_manager.models.client import Client
from apps.risk_manager.models.policy import Policy

class PremiumCredited(models.Model):
    policy = models.ForeignKey(Policy, related_name='crediteds', on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, related_name='premiums_credited', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(null=True)
    amount = models.FloatField(null=True)
    payment_proof = models.FileField(upload_to='premium_credited/', null=True, blank=True)

    def __str__(self):
        return f"{self.policy}, {self.amount}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Premiums Credited"
        db_table = 'premiums_credited'

class PremiumCreditedFile(models.Model):
    premium_credited = models.ForeignKey(PremiumCredited, related_name='files', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='premiums_credited_files/', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ['-date']
        verbose_name_plural = "       Premium Credited Files"
        db_table = 'premiums_credited_files'