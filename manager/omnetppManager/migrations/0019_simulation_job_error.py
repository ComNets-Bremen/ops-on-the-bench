# Generated by Django 3.0.4 on 2020-05-26 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('omnetppManager', '0018_simulation_meta_full'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulation',
            name='job_error',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]