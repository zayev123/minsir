from django.db import models

from apps.client_manager.models.client import Client

class Risk(models.Model):
    client = models.ForeignKey(Client, related_name='risks', on_delete=models.SET_NULL, null=True, blank=True)
    sum_insured = models.FloatField()
    type = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.client}, {self.type}"

    class Meta:
        # ordering = ['-new_renewal_date']
        verbose_name_plural = "       Risks"
        db_table = 'risks'