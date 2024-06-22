from django.db import models

from apps.client_manager.models.client import Client

class ClientStatus(models.Model):
    client = models.ForeignKey(Client, related_name='client_statuses', on_delete=models.SET_NULL, null=True, blank=True)
    current_status = models.CharField(max_length=255)
    status_changed_at = models.DateTimeField()

    def __str__(self):
        return self.client

    class Meta:
        ordering = ['-status_changed_at']
        verbose_name_plural = "       Clients' Statuses"
        db_table = 'client_statuses'