from django.contrib import admin

from .models import Simulation, StorageBackend, ConfigKeyValueStorage, SimOmnetppTemplate

# Register your models here.


# Admin view for Simulations
class SimulationAdmin(admin.ModelAdmin):
    readonly_fields = (
            "simulation_id",
            "summarizing_precision",
            "simulation_error",
            "handled_by",
            "job_error",
            "meta_full",
            "shared_link",
            "storage_backend",
            "runconfig",
            "omnetppini",
            "simulation_timeout",
            "simulation_enqueue_time",
            )

admin.site.register(Simulation, SimulationAdmin)

admin.site.register(StorageBackend)

admin.site.register(ConfigKeyValueStorage)

admin.site.register(SimOmnetppTemplate)
