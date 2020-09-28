from django.contrib import admin

from .models import Simulation, StorageBackend, ConfigKeyValueStorage, SimOmnetppTemplate, OmnetppConfig, OmnetppConfigParameter, OmnetppConfigType

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
            "simulation_start_time",
            )

class OmnetppConfigParameterInline(admin.TabularInline):
    model = OmnetppConfigParameter

class OmnetppConfigAdmin(admin.ModelAdmin):
    inlines = [
            OmnetppConfigParameterInline,
            ]

admin.site.register(Simulation, SimulationAdmin)

admin.site.register(OmnetppConfig, OmnetppConfigAdmin)

admin.site.register(StorageBackend)

admin.site.register(ConfigKeyValueStorage)

admin.site.register(SimOmnetppTemplate)

admin.site.register(OmnetppConfigType)
