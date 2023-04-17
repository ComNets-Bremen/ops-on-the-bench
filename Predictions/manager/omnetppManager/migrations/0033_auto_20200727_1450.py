# Generated by Django 3.0.4 on 2020-07-27 14:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('omnetppManager', '0032_auto_20200727_1415'),
    ]

    operations = [
        migrations.AddField(
            model_name='omnetppconfigtype',
            name='label',
            field=models.CharField(default='<undefined>', max_length=100),
        ),
        migrations.AlterField(
            model_name='omnetppconfigtype',
            name='name',
            field=models.CharField(help_text='Human readable name for this category', max_length=100, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z ]*$', 'Only alphanumeric characters are allowed.')]),
        ),
    ]
