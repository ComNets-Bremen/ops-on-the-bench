from django.urls import path
from django.contrib.auth.decorators import login_required, permission_required

from . import views

from .forms import getOmnetppiniForm, selectSimulationForm

from .views import NewSimWizard

urlpatterns = [
        path('', views.index, name="omnetppManager_index"),
        path('status/', views.status, name="omnetppManager_status"),
        path('new-simulation/', login_required(NewSimWizard.as_view([getOmnetppiniForm, selectSimulationForm])), name="omnetppManager_new-simulation"),
        path('manage_queues/', views.manage_queues, name="omnetppManager_manage_queues"),

        ]



## Currently used URLs

# status: show status of the queues
# new-simulation: create a new simulation
# manage_queues: get all data from the queues (after simulation finished)
