from django.conf import settings

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

from django.core.validators import RegexValidator

import uuid
import json

import datetime

alphanumeric = RegexValidator(r'^[0-9a-zA-Z ]*$', 'Only alphanumeric characters are allowed.')

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
    backend_keep_days = models.PositiveIntegerField(default=7)

    def __str__(self):
        label = str(self.backend_name)
        if self.backend_active:
            label += " (active)"
        return str(label)

## User predefined simulations (templates)
#
# Contains omnetpp.ini files
#
class SimOmnetppTemplate(models.Model):
    template_name = models.CharField(max_length=100)
    template_description = models.TextField(default="")
    template = models.TextField()
    template_active = models.BooleanField(default=False)

    def __str__(self):
        label = str(self.template_name)
        if self.template_active:
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

    job_error = models.TextField(default=None, blank=True, null=True)

    handled_by = models.CharField(max_length=100, default=None, blank=True, null=True)

    notification_mail_address = models.EmailField(default=None, blank=True, null=True)

    storage_backend = models.ForeignKey(StorageBackend, on_delete=models.SET_NULL, null=True, default=None)

    shared_link = models.CharField(max_length=250, default="")

    meta_full = models.TextField(default=None, blank=True, null=True)

    simulation_timeout = models.IntegerField(default=0)

    simulation_enqueue_time = models.DateTimeField(auto_now_add=True)

    simulation_start_time = models.DateTimeField(null=True, default=None)

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

    # Return the meta data in a proper way for the template processing
    def get_meta(self):
        if self.meta_full:
            try:
                # json object?
                return json.loads(self.meta_full)
            except:
                try:
                    # non json object? # TODO: rm eval
                    return eval(self.meta_full)
                except:
                    pass
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

    ## Calculate simulation timeout
    def get_timeout(self):
        return self.simulation_enqueue_time +\
                datetime.timedelta(seconds=self.simulation_timeout)

    ## Return formatted timeout
    def get_simulation_timeout_formatted(self):
        return str(datetime.timedelta(seconds=self.simulation_timeout))


# Type of config (mobility, node etc.)
class OmnetppConfigType(models.Model):

    class Meta:
        ordering = ("order", "-pk",) # Allow manual ordering

    name = models.CharField(
            max_length=100,
            help_text="Human readable name for this category",
            validators=[alphanumeric,],
            )
    label = models.CharField(
            default="<undefined>",
            max_length=100,
            )
    has_multiple_instances = models.BooleanField(
            default=False,
            help_text="Can this category be used several times in one omnetpp.ini?",
            )
    order = models.IntegerField(default=10, help_text="Order the fields manually. Lower number = higher priority")

    def __str__(self):
        return self.name


## Part of omnetpp config
class OmnetppConfig(models.Model):
    class Meta:
        ordering = ("model_type__order","-model_type__pk", "pk") # Order according to higher level model

    name = models.CharField(max_length=100)

    model_type = models.ForeignKey(
            "OmnetppConfigType",
            related_name = "model_type",
            on_delete=models.CASCADE
            )

    def __str__(self):
        params = OmnetppConfigParameter.objects.filter(config=self).count()
        if params > 1:
            return self.name + " with " + str(params) + " parameters"
        else:
            return self.name + " with one parameter"

## Parameters for the selected mobility model
class OmnetppConfigParameter(models.Model):
    class Meta:
        ordering = ("pk",) # Just for clarification

    param_name = models.CharField(max_length=100)
    param_default_value = models.CharField(max_length=100)
    param_unit = models.CharField(max_length=10, default="", blank=True)
    user_editable = models.BooleanField(default=False)

    param_description = models.CharField(default="", max_length=400, blank=True)

    config = models.ForeignKey(
            "OmnetppConfig",
            related_name="parameters",
            on_delete=models.CASCADE
            )

    def __str__(self):
        return self.param_name + "=" + str(self.param_default_value)



# Validator for config code
def is_valid_python(value):
    try:
        eval(value)
    except:
        raise ValidationError(
                _("Invalid python code"),
                )

## Manager class for key value storage access
#
# Tries to access the value from the key value storage. Not defined -> tries to
# access using settings. Not defines -> return None
class ConfigKeyValueStorageManager(models.Manager):
    def get_value(self, key, default=None):
        o = default
        try:
            o = eval(self.model.objects.get(config_key=key).config_value, {}, {})
        except self.model.DoesNotExist:
            # Get key from settings.py
            if hasattr(settings, key):
                o = getattr(settings, key)
        return o

## Simple key value storage management for config (besides settings.py)
class ConfigKeyValueStorage(models.Model):
    config_key = models.CharField(
            max_length = 100,
            unique=True
            )

    config_value = models.CharField(
            max_length = 100,
            validators = [is_valid_python],
            help_text = _("A python expression like \"abc\", [1, 2, 3], True etc."),
            )

    objects = models.Manager()
    config = ConfigKeyValueStorageManager()

    def __str__(self):
        return str(self.config_key) + "=" + str(self.config_value)


## Server config API
class ServerConfig(models.Model):
    server_token = models.UUIDField(
            default=uuid.uuid4,
            help_text="The token for this server",
            )
    server_id = models.SlugField(
            max_length=30,
            unique=True,
            help_text="The server ID, has to be unique",
            )
    server_name = models.CharField(
            max_length=30,
            help_text="A human readable name for this server"
            )

    def __str__(self):
        return self.server_name


class ServerConfigValue(models.Model):
    server = models.ForeignKey(
            "ServerConfig",
            on_delete=models.CASCADE,
            )
    key = models.CharField(
            max_length=30,
            help_text="The key for the value",
            )
    value = models.CharField(
            max_length=30,
            help_text="The value for the key",
            )

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=["server", "key"], name="unique key for server"),
                ]

    def __str__(self):
        return self.server.server_name + ": " + self.key + "=" + self.value

