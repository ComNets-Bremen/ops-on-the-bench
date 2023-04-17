from django.conf import settings

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

from django.core.validators import RegexValidator

from django.core.serializers.json import DjangoJSONEncoder

from django.db.utils import OperationalError

import uuid
import json

import datetime
from django.contrib.auth.models import Group, User



alphanumeric = RegexValidator(r'^[0-9a-zA-Z ]*$', 'Only alphanumeric characters are allowed.')

# Create your models here.

## Model to store data storages
#
# Contains the data storage locations
#
class StorageBackend(models.Model):
    backend_name = models.CharField(max_length=100)
    backend_description = models.TextField(default="", help_text="Human-readable description of the field")
    backend_identifier = models.CharField(max_length=100, default="dropbox", help_text="identifier for the storage backend. Should only be used once")
    backend_token = models.CharField(max_length=100, null=True, blank=True, default=None, help_text="Token (if required)")
    backend_config = models.JSONField(default=str, null=True, blank=True, help_text="Additional information as a json object")
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

    class TerminateReason(models.IntegerChoices):
        NOT_TERMINATED      = 1, _("Simulation not terminated")
        TERMINATED_USER     = 2, _("Terminated by user")
        TERMINATED_EVENTS   = 3, _("Terminated by system: Exceeded events.")
        TERMINATED_CPU      = 4, _("Terminated by system: Exceeded CPU.")
        TERMINATED_RAM      = 5, _("Terminated by system: Exceeded RAM.")
        TERMINATED_DISK     = 6, _("Terminated by system: Exceeded Disk space.")


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

    terminated = models.IntegerField(choices = TerminateReason.choices, default = TerminateReason.NOT_TERMINATED)

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

    simulation_last_update_time = models.DateTimeField(null=True, default=None)

    simulation_state_times = models.TextField(default=None, blank=True, null=True)

    simulation_is_debug_sim = models.BooleanField(
            default=False,
            help_text="Is this a debug simulation? If yes -> ignore for comparison.",
            )
    sim_server = models.CharField(max_length=250, default="")
    
    Predicted_DiskSpace = models.FloatField(default=0)
    Predicted_RAM_Sim = models.FloatField(default=0)
    Predicted_RAM_Res = models.FloatField(default=0)
    Predicted_Time = models.FloatField(default=0)


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


    # Access the scalar stats
    def get_scalar_stats(self, statname):
        meta = self.get_meta()
        if not "scalar_stats" in meta:
            return None

        for s in meta["scalar_stats"]:
            if statname == s[0]:
                return s[-1]

        print("key not found")
        return None

    # Access the simulation runtime stats
    def get_sim_runtime_stats(self, statname):
        meta = self.get_meta()

        if not "sim_runtime_stats" in meta:
            return None
        for s in meta["sim_runtime_stats"]:
            # print(s)
            if statname == s[0]:
                # print(s, s[1])
                return s[1]
        return None

    # Access to the total number of events for the template
    def get_total_events(self):
        return self.get_sim_runtime_stats("totevents")

    # Access simulation runtime
    def get_sim_runtime(self):
        meta = self.get_meta()

        if self.status == 8 or self.status == 3:
            update_time = self.simulation_last_update_time
            update_time = int(update_time.strftime('%s'))
            start_time = self.simulation_start_time
            start_time = int(start_time.strftime('%s'))
            sim_time = update_time - start_time
            sim_time =  "{}".format(str(datetime.timedelta(seconds=sim_time)))
        elif "sim_run_time" in meta and meta["sim_completed_perc"] == 100:
            end_time = int(meta["sim_run_time"])
            start_time = self.simulation_start_time
            start_time = int(start_time.strftime('%s'))
            sim_time = end_time - start_time
            sim_time = "{}".format(str(datetime.timedelta(seconds=sim_time)))
        elif meta["current_state"] == 'SIMULATING' and self.status != 8 and self.status != 3 and "sim_time_sofar" in meta:
            sim_time = int(meta["sim_time_sofar"])
            sim_time = "{}".format(str(datetime.timedelta(seconds=sim_time)))
        else:
            sim_time = ''
    
        return sim_time

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

    ## Return the times when a state changed
    def get_state_times(self):
        times = self.simulation_state_times
        if times:
            return json.loads(self.simulation_state_times)
        else:
            return {}

    ## Add new state change event
    def add_state_times(self, state, time):
        times = self.simulation_state_times
        newTimes = {}
        if times:
            newTimes = json.loads(times)

        newTimes[str(state)] = time
        self.simulation_state_times = json.dumps(newTimes, cls=DjangoJSONEncoder)
        self.save()






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
        except OperationalError:
            pass # when db doesn't exist yet
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



# Benchmark models

# Omnetpp Benchmark configs
class OmnetppBenchmarkConfig(models.Model):

    class Meta:
        ordering = ("order", "-pk",) # Allow manual ordering

    name = models.CharField(
            max_length=100,
            help_text="Sections available on the omnetppbenchmark ini file",
            validators=[alphanumeric,], unique=True,
            )
    label = models.CharField(
            default="<undefined>",
            max_length=100,unique=True,
            help_text="has it is in the Omnetpp Benchmark ini file with the square brackets",
            )
    order = models.IntegerField(default=10, unique=True, help_text="Order the fields manually. Lower number = higher priority")

    def __str__(self):
        return self.name

class OmnetppBenchmarkParameters(models.Model):
    class Meta:
        ordering = ("pk",) 

    param_name = models.CharField(max_length=100)
    param_default_value = models.TextField(max_length=4000,
            help_text="has it is in the Omnetpp Benchmark ini file ( without user editable parameters eg RNG and Forwarding layer)",
            )
    config = models.ForeignKey(
            "OmnetppBenchmarkConfig",
            related_name="BenchmarkParameters",
            on_delete=models.CASCADE
            )

    def __str__(self):
        return self.param_name

class OmnetppBenchmarkEditableParameters(models.Model):
    class Meta:
        ordering = ("pk",) 

    param_name = models.CharField(max_length=100)
    param_default_value = models.CharField(max_length=100)
    param_unit = models.CharField(max_length=10, default="", blank=True)
    user_editable = models.BooleanField(default=False)

    param_description = models.CharField(default="", max_length=400, blank=True)

    config = models.ForeignKey(
            "OmnetppBenchmarkConfig",
            related_name="e_BenchmarkParameters",
            on_delete=models.CASCADE
            )

    def __str__(self):
        return self.param_name

## Configs of OmnetppBenchmark ini Subsections
class OmnetppBenchmarkForwarderConfig(models.Model):

    name = models.CharField(max_length=100,unique=True,)

    def __str__(self):
        return self.name

## Parameters for the OmnetppBenchmark ini Subsections config
class OmnetppBenchmarkForwarderParameters(models.Model):
    class Meta:
        ordering = ("pk",) 
    
    class Param_type(models.IntegerChoices):
        Fixed      = 1, "FIXED"  #non editable by users
        Range    = 2, "RANGE"  #editable by users: within arange of numbers
        Options    = 3, "OPTIONS"   #editable by users: to choose from given option

    param_name = models.CharField(max_length=100)
    param_display_name = models.CharField(max_length=100,default='')
    param_default_value = models.CharField(max_length=100)
    param_unit = models.CharField(max_length=10, default="", blank=True)
    param_type=models.IntegerField(choices=Param_type.choices,default=Param_type.Fixed)
    param_user_option=models.CharField(max_length=100,
            default='None', help_text="users allowed options if not fixed, entered as a list")

    param_description = models.CharField(default="", max_length=400, blank=True)

    config = models.ForeignKey(
            "OmnetppBenchmarkForwarderConfig",
            related_name="ForwarderParameters",
            on_delete=models.CASCADE
            )

    def __str__(self):
        return self.param_name



## make user email unique
User._meta.get_field('email')._unique = True

## create omnetppmanager user profiles
class UserProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.group.name


class UserProfileParameters(models.Model):
    profile = models.ForeignKey(
            "UserProfile",
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
