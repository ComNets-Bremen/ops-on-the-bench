from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from django.db.models import Q

from .models import Simulation, StorageBackend, ConfigKeyValueStorage, SimOmnetppTemplate, OmnetppConfig, OmnetppConfigParameter, OmnetppConfigType, ServerConfig, ServerConfigValue,\
OmnetppBenchmarkSection, OmnetppBenchmarkSubsection, OmnetppBenchmarkSectionConfig, OmnetppBenchmarkSectionParameters , OmnetppBenchmarkSubsectionConfig, OmnetppBenchmarkSubsectionParameters

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

class ServerConfigValueInline(admin.TabularInline):
    model = ServerConfigValue


class ServerConfigAdmin(admin.ModelAdmin):
    inlines = [
            ServerConfigValueInline,
            ]

class OmnetppBenchmarkSectionParametersInline(admin.TabularInline):
    model = OmnetppBenchmarkSectionParameters

class OmnetppBenchmarkSectionAdmin(admin.ModelAdmin):
    inlines = [
            OmnetppBenchmarkSectionParametersInline,
            ]

class OmnetppBenchmarkSubsectionParametersInline(admin.TabularInline):
    model = OmnetppBenchmarkSubsectionParameters

class OmnetppBenchmarkSubsectionAdmin(admin.ModelAdmin):
    inlines = [
            OmnetppBenchmarkSubsectionParametersInline,
            ]
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple, 'queryset' : OmnetppBenchmarkSection.objects.filter(~Q(name='General')) },
    }
    
admin.site.register(Simulation, SimulationAdmin)

admin.site.register(OmnetppConfig, OmnetppConfigAdmin)

admin.site.register(StorageBackend)

admin.site.register(ConfigKeyValueStorage)

admin.site.register(SimOmnetppTemplate)

admin.site.register(OmnetppConfigType)

admin.site.register(ServerConfig, ServerConfigAdmin)

admin.site.register(OmnetppBenchmarkSection)

admin.site.register(OmnetppBenchmarkSubsection)

admin.site.register(OmnetppBenchmarkSectionConfig, OmnetppBenchmarkSectionAdmin)

admin.site.register(OmnetppBenchmarkSubsectionConfig, OmnetppBenchmarkSubsectionAdmin)

