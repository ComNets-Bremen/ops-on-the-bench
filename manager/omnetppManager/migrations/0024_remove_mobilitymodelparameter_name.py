# Generated by Django 3.0.4 on 2020-07-27 12:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('omnetppManager', '0023_mobilitymodel_mobilitymodelparameter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mobilitymodelparameter',
            name='name',
        ),
    ]
