from django.db import models

from apps.risk_manager.models.clause_category import ClauseCategory
from apps.risk_manager.models.policy import Policy

class ImportantClause(models.Model):
    policy = models.ForeignKey(Policy, related_name='clauses', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(ClauseCategory, related_name='clauses', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}, {self.policy}"

    class Meta:
        # ordering = ['-new_renewal_date']
        verbose_name_plural = "       Important Clauses"
        db_table = 'important_clauses'