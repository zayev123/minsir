from django.db import models

from apps.risk_manager.models.policy import Policy
from apps.risk_manager.models.premium_credited import PremiumCredited

class CommissionRealized(models.Model):
    policy = models.ForeignKey(Policy, related_name='commissions', on_delete=models.SET_NULL, null=True, blank=True)
    premium_credited = models.OneToOneField(PremiumCredited, related_name='commission', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.FloatField()

    def __str__(self):
        return f"{self.policy}, {self.amount}"

    class Meta:
        # ordering = ['-status_changed_at']
        verbose_name_plural = "       Commissions Realized"
        db_table = 'commissions_realized'