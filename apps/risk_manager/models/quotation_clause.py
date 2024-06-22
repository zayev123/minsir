from django.db import models

from apps.risk_manager.models.clause_category import ClauseCategory
from apps.risk_manager.models.quotation import Quotation

class QuotationClause(models.Model):
    quotation = models.ForeignKey(Quotation, related_name='qlauses', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(ClauseCategory, related_name='qlauses', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ['-new_renewal_date']
        verbose_name_plural = "       Quotation Clauses"
        db_table = 'quotation_clauses'