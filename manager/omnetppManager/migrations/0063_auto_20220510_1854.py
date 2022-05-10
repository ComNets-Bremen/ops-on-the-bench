# Generated by Django 3.2.13 on 2022-05-10 18:54

from django.db import migrations
from django.contrib.auth.models import Group
import logging
from django.core.management.sql import emit_post_migrate_signal

logger = logging.getLogger(__name__)

# initial user profile groups
user_profile_groups = ["Staff User", "Simple User"]

## create initial groups during migration i.e data migration
def add_groups(apps, schema_editor):
    # https://code.djangoproject.com/ticket/23422
    # db_alias = schema_editor.connection.alias
    # try:
    #     emit_post_migrate_signal(2, False, 'default')
    # except TypeError:  # Django < 1.8
    #     emit_post_migrate_signal([], 2, False, 'default', db_alias)

    for group in user_profile_groups:
        role, created = Group.objects.get_or_create(name=group)
        logger.info(f'{group} Group created')
        role.save()

class Migration(migrations.Migration):

    dependencies = [
        # depends on '0001_initial'
        ('omnetppManager', '0001_initial'),
        ('omnetppManager', '0062_auto_20220509_1147'),
    ]

    operations = [
        migrations.RunPython(add_groups)
    ]
