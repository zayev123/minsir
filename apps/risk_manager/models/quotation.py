from django.db import models

from apps.account_manager.models.insurance_company import InsuranceCompany
from apps.risk_manager.models.risk import Risk

class Quotation(models.Model):
    insurance_company = models.ForeignKey(InsuranceCompany, related_name='quotations', on_delete=models.SET_NULL, null=True, blank=True)
    risk = models.ForeignKey(Risk, related_name='quotations', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    quoted_rate = models.FloatField()
    line_written = models.FloatField()
    share_percentage = models.FloatField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.risk}, {self.quoted_rate}"

    class Meta:
        # ordering = ['-new_renewal_date']
        verbose_name_plural = "       Quotations"
        db_table = 'quotations'