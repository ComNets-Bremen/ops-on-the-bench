from django.contrib import admin

from .models import Simulation

# Register your models here.


# Admin view for Simulations
class SimulationAdmin(admin.ModelAdmin):
    readonly_fields = ("simulation_id",)

admin.site.register(Simulation, SimulationAdmin)
