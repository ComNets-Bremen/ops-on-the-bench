from django.conf import settings

from django.db import models

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
