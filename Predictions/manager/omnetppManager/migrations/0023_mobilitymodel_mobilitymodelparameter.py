# Generated by Django 3.0.4 on 2020-07-27 12:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('omnetppManager', '0022_simulation_simulation_start_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='MobilityModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='MobilityModelParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('param_name', models.CharField(max_length=100)),
                ('param_default_value', models.CharField(max_length=100)),
                ('mobility_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='omnetppManager.MobilityModel')),
            ],
        ),
    ]
