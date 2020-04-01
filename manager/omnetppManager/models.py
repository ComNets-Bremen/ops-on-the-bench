from django.conf import settings

from django.db import models
from django.utils.translation import gettext as _

import uuid

# Create your models here.


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

    user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            )
    title = models.CharField(max_length=100)
    omnetppini = models.TextField()
    runconfig = models.CharField(max_length=100)
    simulation_id = models.UUIDField(
            editable=False,
            default=uuid.uuid4
            )
    status = models.IntegerField(choices=Status.choices, default=Status.UNKNOWN)

    # String representation, mainly for debugging and admin model
    def __str__(self):
        return "Simulation " + str(self.simulation_id) + " started by user " + str(self.user)


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

