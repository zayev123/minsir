# Generated by Django 5.0.6 on 2024-07-03 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_manager', '0003_alter_policyfile_file_alter_policyfile_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='policy',
            name='commission_type',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='policy',
            name='commission_value',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='policy',
            name='issue_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='policy',
            name='net_premium',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='policy',
            name='renewal_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='premiumcredited',
            name='amount',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='premiumcredited',
            name='date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='premiumcredited',
            name='payment_proof',
            field=models.FileField(blank=True, null=True, upload_to='premium_credited/'),
        ),
        migrations.AlterField(
            model_name='premiumdebited',
            name='amount',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='premiumdebited',
            name='date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='premiumdebited',
            name='payment_proof',
            field=models.FileField(blank=True, null=True, upload_to='premium_debited/'),
        ),
    ]
