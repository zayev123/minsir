# Generated by Django 5.0.6 on 2024-07-03 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_manager', '0006_alter_premiumcreditedfile_table'),
    ]

    operations = [
        migrations.AlterField(
            model_name='premiumcreditedfile',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='premiums_credited_files/'),
        ),
    ]