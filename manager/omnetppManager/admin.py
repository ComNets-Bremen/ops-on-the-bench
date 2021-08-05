from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models
from django.db.models import Q

from .models import Simulation, StorageBackend, ConfigKeyValueStorage, SimOmnetppTemplate, OmnetppConfig, OmnetppConfigParameter, OmnetppConfigType, ServerConfig, ServerConfigValue,\
OmnetppBenchmarkSection, OmnetppBenchmarkSubsection, OmnetppBenchmarkSectionConfig, OmnetppBenchmarkSectionParameters , OmnetppBenchmarkSubsectionConfig, OmnetppBenchmarkSubsectionParameters,\
OmnetppBenchmarkConfig, OmnetppBenchmarkParameters, OmnetppBenchmarkEditableParameters, OmnetppBenchmarkForwarderConfig, OmnetppBenchmarkForwarderParameters
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
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

class OmnetppBenchmarkSubsectionParametersInline(admin.TabularInline):
    model = OmnetppBenchmarkSubsectionParameters

class OmnetppBenchmarkSubsectionAdmin(admin.ModelAdmin):
    inlines = [
            OmnetppBenchmarkSubsectionParametersInline,
            ]
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple, 'queryset' : OmnetppBenchmarkSection.objects.filter(~Q(name='General')) },
    }
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

# Hiding a model from the admin index site
class OmnetppBenchmarkSectAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

class OmnetppBenchmarkParametersInline(admin.TabularInline):
    model = OmnetppBenchmarkParameters
    extra = 0

class OmnetppBenchmarkEditableParametersInline(admin.TabularInline):
    model = OmnetppBenchmarkEditableParameters
    extra = 0

class OmnetppBenchmarkParametersAdmin(admin.ModelAdmin):
    inlines = [
            OmnetppBenchmarkParametersInline,
            OmnetppBenchmarkEditableParametersInline
            ]
            
class OmnetppBenchmarkForwarderParametersInline(admin.TabularInline):
    model = OmnetppBenchmarkForwarderParameters
    extra = 0

class OmnetppBenchmarkForwarderParametersAdmin(admin.ModelAdmin):
    inlines = [
            OmnetppBenchmarkForwarderParametersInline,
            ]
    
admin.site.register(Simulation, SimulationAdmin)

admin.site.register(OmnetppConfig, OmnetppConfigAdmin)

admin.site.register(StorageBackend)

admin.site.register(ConfigKeyValueStorage)

admin.site.register(SimOmnetppTemplate)

admin.site.register(OmnetppConfigType)

admin.site.register(ServerConfig, ServerConfigAdmin)

admin.site.register(OmnetppBenchmarkSection,OmnetppBenchmarkSectAdmin)

admin.site.register(OmnetppBenchmarkSubsection,OmnetppBenchmarkSectAdmin)

admin.site.register(OmnetppBenchmarkSectionConfig, OmnetppBenchmarkSectionAdmin)

admin.site.register(OmnetppBenchmarkSubsectionConfig, OmnetppBenchmarkSubsectionAdmin)

admin.site.register(OmnetppBenchmarkConfig, OmnetppBenchmarkParametersAdmin)

admin.site.register(OmnetppBenchmarkForwarderConfig, OmnetppBenchmarkForwarderParametersAdmin)
