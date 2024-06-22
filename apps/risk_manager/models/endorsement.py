from django.db import models

from apps.risk_manager.models.policy import Policy

class Endorsement(models.Model):
    policy = models.ForeignKey(Policy, related_name='endorsements', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    new_renewal_date = models.DateTimeField()
    number = models.CharField(max_length=255)
    file = models.FileField(upload_to='endorsements/')
    description = models.TextField(blank=True, null=True)
    new_net_premium = models.FloatField()

    def __str__(self):
        return f"{self.policy}, {self.date}"

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "       Endorsements"
        db_table = 'endorsements'