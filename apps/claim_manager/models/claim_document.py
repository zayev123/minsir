from django.db import models
from datetime import datetime
from apps.claim_manager.models.claim import Claim

class ClaimDocument(models.Model):
    claim = models.ForeignKey(Claim, related_name='documents', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='claim_documents/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.name}, {self.claim}"

    class Meta:
        # ordering = ['-date']
        verbose_name_plural = "       Claims' Documents"
        db_table = 'claim_documents'