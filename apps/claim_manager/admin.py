from django.contrib import admin

from apps.claim_manager.models.claim import Claim
from apps.claim_manager.models.claim_credited import ClaimCredited
from apps.claim_manager.models.claim_debited import ClaimDebited
from apps.claim_manager.models.claim_document import ClaimDocument

@admin.register(ClaimCredited)
class ClaimCreditedAdmin(admin.ModelAdmin):
    list_display = ['id', 'claim', 'insurance_line', 'date']
    search_fields = ['id', 'date']

@admin.register(ClaimDebited)
class ClaimDebitedAdmin(admin.ModelAdmin):
    list_display = ['id', 'claim', 'date', 'amount']
    search_fields = ['id', 'date']

@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'claim', 'name']
    search_fields = ['id', 'name']

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['id', 'policy', 'date_of_intimation', 'cash_call_amount']
    search_fields = ['id', 'date_of_intimation']
