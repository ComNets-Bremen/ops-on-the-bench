from django.urls import path, reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import views as auth_views
from .decorators import already_authenticated, auth_required

from . import views

from .forms import getOmnetppiniForm, selectSimulationForm,getOmnetppBenchmarkSection,selectForwarderForm, BenchmarkGeneralSettingForm,UserEditorForm, ModelPredictionForm

from .views import NewSimWizard, JobDetailView, DetailSimWizard, BenchSimWizard

urlpatterns = [
        path('', views.index, name="omnetppManager_index"),
        path('queue_status/', views.queue_status, name="omnetppManager_queue_status"),
        path('job_status/', views.job_status, name="omnetppManager_job_status"),
        path('new-simulation/', auth_required(NewSimWizard.as_view([getOmnetppiniForm, selectSimulationForm, ModelPredictionForm])), name="omnetppManager_new-simulation"),
        path('manage_queues/', views.manage_queues, name="omnetppManager_manage_queues"),
        path('manage_queues/<output_format>/', views.manage_queues, name="omnetppManager_manage_queues"),
        path('job-details/<int:pk>/', auth_required(JobDetailView.as_view()), name='job-details'),
        path('job-kill/<int:pk>/', views.job_kill, name='job-kill'),
        path('newsim-detail/', auth_required(DetailSimWizard.as_view()), name="omnetppManager_detail_sim"),
        path('get-server-config/', views.get_server_config, name="omnetppManager_get_server_config"),
        path('get-simulation-details/',views.get_simulation_details, name="omnetppManager_get_simulation_details"),
        path('get-server-resources/',views.get_server_resources, name="omnetppManager_get_server_resources"),
        path('export-simulation-stats/', views.export_simulation_stats, name="omnetppManager_export_simulation_stats"),
        path('request-access/', views.request_access, name="omnetppManager_request_access"),
        path('request-access-thanks/', views.request_access_thanks, name="omnetppManager_request_access_thanks"),
        path('register/', views.register_users, name="omnetppManager_register"),
        path('login/', views.login_users, name="omnetppManager_login"),
        path('logout/', views.logout_users, name="omnetppManager_logout"),
        path('change-password/', views.change_password, name="omnetppManager_change_password"),
        path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),
        path('resend-activation/', views.resend_activation, name='resend_activation'),
        path('reset-password/', already_authenticated(views.ResetPassword.as_view()), name="omnetppManager_reset_password"),
        path('password-reset-confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html',
                success_url = reverse_lazy('omnetppManager_password_reset_complete')),name='omnetppManager_password_reset_confirm'),
        path('password-reset-complete/',auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
                name='omnetppManager_password_reset_complete'),
        path('rerun-sim/<int:pk>', views.rerun_simulation, name="omnetppManager_rerun_sim"),
        path('benchmark-simulation/', auth_required(BenchSimWizard.as_view([getOmnetppBenchmarkSection, selectForwarderForm,UserEditorForm,BenchmarkGeneralSettingForm,])), name="omnetppManager_benchmark-simulation"),
        path('get-profile-parameter/', views.get_profile_parameters, name="omnetppManager_get_profile_parameters"),
        ]


## Currently used URLs
# status: show status of the queues
# new-simulation: create a new simulation
# manage_queues: get all data from the queues (after simulation finished)
# benchmark-simulation: create a new benchmark simulation
