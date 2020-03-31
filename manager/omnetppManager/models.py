from django.conf import settings

from django.db import models

import uuid

# Create your models here.

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
