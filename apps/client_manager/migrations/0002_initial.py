# Generated by Django 5.0.6 on 2024-06-22 10:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account_manager', '0002_insurancecompany'),
        ('client_manager', '0001_initial'),
        ('risk_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientdocument',
            name='risk',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='risk_manager.risk'),
        ),
        migrations.AddField(
            model_name='clientstatus',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_statuses', to='client_manager.client'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meetings', to='client_manager.client'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='insurance_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meetings', to='account_manager.insurancecompany'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='risk',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meetings', to='risk_manager.risk'),
        ),
    ]