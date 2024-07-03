from django.contrib import admin

from apps.risk_manager.models.agent_revenue import AgentRevenue
from apps.risk_manager.models.clause_category import ClauseCategory
from apps.risk_manager.models.commission_realized import CommissionRealized
from apps.risk_manager.models.endorsement import Endorsement
from apps.risk_manager.models.important_clause import ImportantClause
from apps.risk_manager.models.insurance_line import InsuranceLine
from apps.risk_manager.models.policy import Policy, PolicyFile
from apps.risk_manager.models.premium_credited import PremiumCredited, PremiumCreditedFile
from apps.risk_manager.models.premium_debited import PremiumDebited
from apps.risk_manager.models.quotation import Quotation
from apps.risk_manager.models.quotation_clause import QuotationClause
from apps.risk_manager.models.risk import Risk

@admin.register(AgentRevenue)
class AgentRevenueAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent', 'commission_realized']
    search_fields = ['id',]

@admin.register(ClauseCategory)
class ClauseCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',]
    search_fields = ['id', 'name']

@admin.register(CommissionRealized)
class CommissionRealizedAdmin(admin.ModelAdmin):
    list_display = ['id', 'policy', 'premium_credited']
    search_fields = ['id',]

@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = ['id', 'policy', 'date']
    search_fields = ['id', 'date']

@admin.register(ImportantClause)
class ImportantClauseAdmin(admin.ModelAdmin):
    list_display = ['id', 'policy', 'name']
    search_fields = ['id', 'name']

@admin.register(InsuranceLine)
class InsuranceLineAdmin(admin.ModelAdmin):
    list_display = ['id', 'policy', 'date', 'line_written']
    search_fields = ['id', 'date']

@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['id', 'risk', 'issue_date', 'number']
    search_fields = ['id', 'issue_date', 'number']

@admin.register(PolicyFile)
class PolicyFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'policy', 'name']
    search_fields = ['id', 'policy__number', 'name']

@admin.register(PremiumCredited)
class PremiumCreditedAdmin(admin.ModelAdmin):
    list_display = ['id', 'policy', 'date', 'amount']
    search_fields = ['id', 'date']

@admin.register(PremiumCreditedFile)
class PremiumCreditedFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'premium_credited', 'name']
    search_fields = ['id', 'name']

@admin.register(PremiumDebited)
class PremiumDebitedAdmin(admin.ModelAdmin):
    list_display = ['id', 'insurance_line', 'date', 'amount']
    search_fields = ['id', 'date']

@admin.register(QuotationClause)
class QuotationClauseAdmin(admin.ModelAdmin):
    list_display = ['id', 'quotation', 'name',]
    search_fields = ['id', 'name']

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['id', 'insurance_company', 'risk', 'date', 'line_written']
    search_fields = ['id', 'insurance_company__name']


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'sum_insured', 'type']
    search_fields = ['id', 'type']
