# Generated by Django 5.0.6 on 2024-07-03 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client_manager', '0003_alter_client_agent_alter_client_connected_through_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]