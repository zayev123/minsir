from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.client_manager.models.client import Client
from apps.risk_manager.models.risk import Risk

class EmailData(models.Model):
    from_email = models.CharField(max_length=255)
    to_emails = ArrayField(models.CharField(max_length=255), blank=True, default=list)
    date = models.DateTimeField(null=True)
    subject = models.TextField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.subject

    class Meta:
        # ordering = ['-date']
        verbose_name_plural = "       Emails Data"
        db_table = 'emails'


class EmailAttachment(models.Model):
    email = models.ForeignKey(EmailData, related_name='attachments', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='email_attachments/')

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ['-date']
        verbose_name_plural = "       Email Attachments"
        db_table = 'email_attachments'