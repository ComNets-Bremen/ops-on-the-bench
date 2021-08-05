from django.urls import path
from django.contrib.auth.decorators import login_required, permission_required

from . import views

from .forms import getOmnetppiniForm, selectSimulationForm,getOmnetppBenchmarkSection,selectForwarderForm, BenchmarkGeneralSettingForm

from .views import NewSimWizard, JobDetailView, DetailSimWizard, BenchSimWizard

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
        path('get-server-config/', views.get_server_config, name="omnetppManager_get_server_config"),
        path('export-simulation-stats/', views.export_simulation_stats, name="omnetppManager_export_simulation_stats"),
        path('request-access/', views.request_access, name="omnetppManager_request_access"),
        path('request-access-thanks/', views.request_access_thanks, name="omnetppManager_request_access_thanks"),
        path('rerun-sim/<int:pk>', views.rerun_simulation, name="omnetppManager_rerun_sim"),
        path('benchmark-simulation/', login_required(BenchSimWizard.as_view([getOmnetppBenchmarkSection, selectForwarderForm,BenchmarkGeneralSettingForm,])), name="omnetppManager_benchmark-simulation"),
        ]


## Currently used URLs

# status: show status of the queues
# new-simulation: create a new simulation
# manage_queues: get all data from the queues (after simulation finished)
# benchmark-simulation: create a new benchmark simulation
