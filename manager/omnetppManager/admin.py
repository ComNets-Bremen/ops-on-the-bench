from django.contrib import admin

from .models import Simulation, StorageBackend

# Register your models here.


# Admin view for Simulations
class SimulationAdmin(admin.ModelAdmin):
    readonly_fields = ("simulation_id", "simulation_error", "handled_by",)

admin.site.register(Simulation, SimulationAdmin)

admin.site.register(StorageBackend)
