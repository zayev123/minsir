from django.contrib import admin

from apps.email_manager.models.email import EmailAttachment, EmailData

@admin.register(EmailData)
class EmailDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'from_email', 'subject', 'to_emails']
    search_fields = ['id', 'from_email', 'subject', 'to_emails']

@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'name',]
    search_fields = ['id', 'name', "email__subject"]
