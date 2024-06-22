from django.db import models

from apps.risk_manager.models.risk import Risk

class Policy(models.Model):
    risk = models.ForeignKey(Risk, related_name='policies', on_delete=models.SET_NULL, null=True, blank=True)
    issue_date = models.DateTimeField()
    renewal_date = models.DateTimeField()
    number = models.CharField(max_length=255)
    file = models.FileField(upload_to='policies/')
    description = models.TextField(blank=True, null=True)
    net_premium = models.FloatField()
    commission_type = models.CharField(max_length=255)
    commission_value = models.FloatField()

    def __str__(self):
        return f"{self.number}, {self.risk}"

    class Meta:
        ordering = ['-issue_date']
        verbose_name_plural = "       Policies"
        db_table = 'policies'