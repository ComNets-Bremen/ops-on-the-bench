# Generated by Django 3.0.4 on 2020-05-26 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('omnetppManager', '0017_auto_20200525_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulation',
            name='meta_full',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
