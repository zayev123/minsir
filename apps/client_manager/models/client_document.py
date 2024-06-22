from django.db import models

from apps.client_manager.models.client import Client
from apps.risk_manager.models.risk import Risk

class ClientDocument(models.Model):
    client = models.ForeignKey(Client, related_name='documents', on_delete=models.SET_NULL, null=True, blank=True)
    risk = models.ForeignKey(Risk, related_name='documents', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='client_documents/')

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ['-date']
        verbose_name_plural = "       Clients' Documents"
        db_table = 'client_documents'