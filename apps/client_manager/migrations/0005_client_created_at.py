# Generated by Django 5.0.6 on 2024-07-09 05:56

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client_manager', '0004_client_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2023, 1, 1, 0, 0)),
        ),
    ]