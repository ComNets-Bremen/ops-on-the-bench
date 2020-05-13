from django.conf import settings

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

import uuid

# Create your models here.

## Model to store data storages
#
# Contains the data storage locations
#
class StorageBackend(models.Model):
    backend_name = models.CharField(max_length=100)
    backend_description = models.TextField(default="")
    backend_identifier = models.CharField(max_length=100, default="dropbox")
    backend_token = models.CharField(max_length=100, null=True, blank=True, default=None)
    backend_active = models.BooleanField(default=False)

    def __str__(self):
        label = str(self.backend_name)
        if self.backend_active:
            label += " (active)"
        return str(label)

## Model to store Simulation details
#
# Stores the following data
# - user        : Reference to user who started the simulation
# - title       : Meaningful name of the simulation
# - omnetppini  : The omnetppini as a long text
# - runconfig   : Name of the config from the omnetpp.ini file
# - simulationid: The id given by the queue
class Simulation(models.Model):
    class Meta:
        ordering = ["-pk",]

    class Status(models.IntegerChoices):
        QUEUED      = 1, _("queued")
        FINISHED    = 2, _("finished")
        FAILED      = 3, _("failed")
        STARTED     = 4, _("started")
        DEFERRED    = 5, _("deferred")
        SCHEDULED   = 6, _("scheduled")
        UNKNOWN     = 7, _("unknown")
        ABORTED     = 8, _("aborted")

    user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            )
    title           = models.CharField(max_length=100)
    omnetppini      = models.TextField()
    runconfig       = models.CharField(max_length=100)
    summarizing_precision = models.FloatField(default=100)
    simulation_id   = models.UUIDField(
            editable=False,
            default = uuid.uuid4
            )
    status = models.IntegerField(choices=Status.choices, default=Status.UNKNOWN)

    simulation_error = models.TextField(default=None, blank=True, null=True)

    handled_by = models.CharField(max_length=100, default=None, blank=True, null=True)

    notification_mail_address = models.EmailField(default=None, blank=True, null=True)

    storage_backend = models.ForeignKey(StorageBackend, on_delete=models.SET_NULL, null=True, default=None)

    shared_link = models.CharField(max_length=250, default="")

    # String representation, mainly for debugging and admin model
    def __str__(self):
        return "Simulation " + str(self.simulation_id) + " started by user " + str(self.user)

    # Return url for detail view
    def get_absolute_url(self):
        return reverse('job-details', kwargs={
            'pk' : self.pk
            })

    ## Has shared link
    def get_shared_link(self):
        if self.shared_link and self.shared_link != "":
            return self.shared_link
        return None

    ## Notify user on sim state change
    def send_notify_mail(self):
        return self.notification_mail_address not in ["", None]

    ## status for template rendering: queued
    def is_queued(self):
        return self.status == self.Status.QUEUED

    ## status for template rendering: finished
    def is_finished(self):
        return self.status == self.Status.FINISHED

    ## status for template rendering: failed
    def is_failed(self):
        return self.status == self.Status.FAILED

    ## status for template rendering: started
    def is_started(self):
        return self.status == self.Status.STARTED

    ## status for template rendering: deferred
    def is_deferred(self):
        return self.status == self.Status.DEFERRED

    ## status for template rendering: scheduled
    def is_scheduled(self):
        return self.status == self.Status.SCHEDULED

    ## status for template rendering: aborted
    def is_aborted(self):
        return self.status == self.Status.ABORTED


## Simple key value storage management for config (besides settings.py)
class ConfigKeyValueStorage(models.Model):
    config_key = models.CharField(
            max_length = 100,
            unique=True
            )

    config_value = models.CharField(
            max_length = 100
            )

    def __str__(self):
        return str(self.config_key)

    #TODO: Handle data types and return correspondingly



