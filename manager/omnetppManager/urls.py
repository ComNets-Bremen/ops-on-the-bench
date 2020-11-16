from django.urls import path
from django.contrib.auth.decorators import login_required, permission_required

from . import views

from .forms import getOmnetppiniForm, selectSimulationForm

from .views import NewSimWizard, JobDetailView, DetailSimWizard

urlpatterns = [
        path('', views.index, name="omnetppManager_index"),
        path('queue_status/', views.queue_status, name="omnetppManager_queue_status"),
        path('job_status/', views.job_status, name="omnetppManager_job_status"),
        path('new-simulation/', login_required(NewSimWizard.as_view([getOmnetppiniForm, selectSimulationForm])), name="omnetppManager_new-simulation"),
        path('manage_queues/', views.manage_queues, name="omnetppManager_manage_queues"),
        path('manage_queues/<output_format>/', views.manage_queues, name="omnetppManager_manage_queues"),
        path('job-details/<int:pk>/', login_required(JobDetailView.as_view()), name='job-details'),
        path('job-kill/<int:pk>/', views.job_kill, name='job-kill'),
        path('newsim-detail/', login_required(DetailSimWizard.as_view()), name="omnetppManager_detail_sim"),
        ]



## Currently used URLs

# status: show status of the queues
# new-simulation: create a new simulation
# manage_queues: get all data from the queues (after simulation finished)
