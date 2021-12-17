from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.utils.html import strip_tags
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import Group
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .decorators import already_authenticated, auth_required
from django.forms import formset_factory
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin

from django.core.mail import send_mail

from formtools.wizard.views import SessionWizardView

from .models import Simulation, StorageBackend, ConfigKeyValueStorage, ServerConfig, ServerConfigValue,\
     OmnetppBenchmarkConfig, OmnetppBenchmarkParameters, OmnetppBenchmarkEditableParameters, OmnetppBenchmarkForwarderConfig, OmnetppBenchmarkForwarderParameters

from .forms import getOmnetppiniForm, selectSimulationForm,getOmnetppBenchmarkSection,selectForwarderForm, BenchmarkGeneralSettingForm,UserEditorForm

from rq import Queue
from redis import Redis

import configparser

import io

import json

import os
from django.core.exceptions import SuspiciousOperation

import datetime, time
import pytz

from .forms import getOmnetppiniForm, selectSimulationForm, NodeSettingForm, GeneralSettingForm, ModelDetailSettingForm, BaseNodeSettingFormSet, RequestAccessForm, RerunSimForm,\
    CreateUsers

from utils.worker import run_simulation, SimulationRuntimes

# Create your views here.

## Redirect app from / -> /omnetppManager
def redirect_to_here(request):
    return HttpResponseRedirect(reverse("omnetppManager_index"))

## Index page
def index(request):
    return render(request, 'omnetppManager/index.html', {'title':"Overview"})

def request_access(request):
    form = None
    if request.method == "POST":
        form = RequestAccessForm(request.POST)
        if form.is_valid():
            msg = "Request for demo access\n\n"
            for field in form.cleaned_data:
                msg += field + ": " + str(form.cleaned_data[field]) + "\n\n"

            send_mail(
                'Demo Access Request',
                msg,
                str(form.cleaned_data["mail"]),
                [ConfigKeyValueStorage.config.get_value("DEFAULT_RECEIVER_MAIL_ADDRESS"),],
                fail_silently=False,
            )
            return HttpResponseRedirect(reverse('omnetppManager_request_access_thanks'))

    if not form:
        form = RequestAccessForm()

    return render(request, 'omnetppManager/request_access.html', {'form': form, 'title': "Request demo access"})

def request_access_thanks(request):
    return render(request, 'omnetppManager/request_access_thanks.html', {'title': "Thanks for your request"})

## User registration
@already_authenticated
def register_users(request):
    form = CreateUsers()
    
    if request.method == 'POST':
        form = CreateUsers(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            group = Group.objects.get(name='Simple User')
            user.groups.add(group)
            messages.success(request, 'Account successfully created for ' + username)
            return redirect('omnetppManager_login')
    context= {'form': form}
    return render(request,'registration/register_users.html', context)


## User login
@already_authenticated
def login_users(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username = username, password = password)

        if user != None:
            login(request, user)
            return redirect('omnetppManager_index')
        else:
            messages.info(request,'username or password is incorrect, try again!')
    return render(request, 'registration/login.html')


## User logout
def logout_users(request):
    logout(request)
    return redirect('omnetppManager_login')

## change password view
@auth_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('omnetppManager_change_password')
        else:
            messages.error(request, 'Please correct the error(s) below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context= {'form': form}
    return render(request, 'registration/change_password.html', context)

## reset password
class ResetPassword(SuccessMessageMixin, PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_message = "We have emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you do not receive an email, " \
                      "please make sure you have entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('omnetppManager_index')

## Show status of queues
@login_required
def queue_status(request):
    status = []

    q = Queue(connection=get_redis_conn())

    status.append({
        "name" : "Queued jobs",
        "number" : len(q),
        })
    status.append({
        "name" : "Finished jobs",
        "number" : len(q.finished_job_registry),
        })
    status.append({
        "name" : "Failed jobs",
        "number" : len(q.failed_job_registry),
        })
    status.append({
        "name" : "Started jobs",
        "number" : len(q.started_job_registry),
        })
    status.append({
        "name" : "Deferred jobs",
        "number" : len(q.deferred_job_registry),
        })
    status.append({
        "name" : "Scheduled jobs",
        "number" : len(q.scheduled_job_registry),
        })

    return render(request, 'omnetppManager/queue_status_page.html', {
            "status" : status,
            "title"  : "Queue status",
        })

## Show status of jobs
@login_required
def job_status(request):
    simulations = Simulation.objects.all()
    paginator = Paginator(simulations, 25) # 25 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "omnetppManager/job_status_page.html",
            {
                "jobs" : page_obj,
                "title" : "Job status",
            })


## Manage the queues and get the results from the queue.
#
# No login required: Can be called from a script. Therefore, only little
# information is given
#
# TODO: Increase security?
def manage_queues(request, output_format="json"):

    return_values = sync_simulations()

    if output_format == "json":
        return JsonResponse(return_values)
    else: # http output
        return render(
            request,
            'omnetppManager/manage_queues.html',
            return_values
            )


## Export all simulation data as a json object
@login_required
def export_simulation_stats(request):
    results = {}
    results["export_time"] = time.time()
    results["export_server"] = request.META["REMOTE_ADDR"]
    results["simulations"] = []
    for sim in Simulation.objects.filter(status = Simulation.Status.FINISHED).order_by("-id"):
        s = dict()
        s["title"] = sim.title
        s["omnetppini"] = sim.omnetppini
        s["runconfig"] = sim.runconfig
        s["exec_server"] = sim.handled_by
        s["sim_start_time"] = sim.simulation_start_time
        s["sim_last_update"] = sim.simulation_last_update_time
        s["sim_state_times"] = sim.simulation_state_times
        s["meta"] = sim.get_meta()
        s["sim_id"] = sim.simulation_id
        results["simulations"].append(s)

    response = JsonResponse(results)
    response["Content-Disposition"] = 'attachment; filename=simulation-meta.json'
    return response

## Kill queues sims
#
# Tries to kill a simulation. Currently only kills queued sims
# TODO: Extend, kill all kind of simulations
# TODO: Ask if it is okay to kill the sim
# TODO: Ensure the user has the right permissions
@login_required
@require_http_methods(["POST",])
def job_kill(request, pk):
    simulation = get_object_or_404(
            Simulation,
            pk=pk
            )
    print("Trying to kill simulation", simulation.simulation_id)

    q = Queue(connection=get_redis_conn())

    if q.remove(str(simulation.simulation_id)) > 0:
        # We removed one job. update status:
        update_sim_status(
                simulation.simulation_id,
                Simulation.Status.ABORTED,
                Simulation.TerminateReason.TERMINATED_USER
                )
    else:
        print("Not able to remove simulation from queue", len(q))

    return HttpResponseRedirect(reverse("omnetppManager_job_status"))


@login_required
def rerun_simulation(request, pk):
    form = None

    simulation = get_object_or_404(
            Simulation,
            pk=pk
            )


    if request.method == "POST":
        form = RerunSimForm(request.POST)
        if form.is_valid():
            # Start new sim derived from old config
            simulation.pk = None # store as new object
            args = {
                    "user" : str(request.user),
                    "title" : str(form.cleaned_data["simulation_title"]),
                    "omnetpp.ini" : str(simulation.omnetppini),
                    "runconfig" : str(simulation.runconfig),
                    "summarizing_precision" : float(simulation.summarizing_precision),
                    "storage_backend" : str(simulation.storage_backend.backend_name),
                    "storage_backend_id" : str(simulation.storage_backend.backend_identifier),
                    "storage_backend_token" : str(simulation.storage_backend.backend_token),
                    "storage_backend_keep_days" : str(simulation.storage_backend.backend_keep_days),
                    }


            print("Simulation arguments:", args)
            q = Queue(connection=get_redis_conn())
            # Start job
            job = q.enqueue(
                    run_simulation,
                    SimulationRuntimes.OPS_KEETCHI,
                    args,
                    job_timeout=ConfigKeyValueStorage.config.get_value("DEFAULT_SIMULATION_TIMEOUT"),
                    )
            print("Job with id", job.id, "started")

            simulation.user = request.user
            simulation.title = form.cleaned_data["simulation_title"]
            simulation.simulation_id = job.id
            simulation.simulation_timeout = job.timeout

            simulation.save()
            sync_simulations()

            return redirect(simulation.get_absolute_url())

    if not form:

        form = RerunSimForm(initial={
            "simulation_title" : simulation.title+"_rerun",
            })

    return render(request, 'omnetppManager/rerun_simulation.html', {'form': form, 'title': "Rerun Simulation", 'pk':pk})








## Start a new simulation using the form wizard module
#
# view is created directly in the urls.py
class NewSimWizard(SessionWizardView):
    # Store the omnetpp.ini files temporarily. TODO: Ensure they are removed
    # everytime
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_omnetppini_files'))
    template_name = 'omnetppManager/start_simulation.html'

    # Get the sections from the omnetpp.ini for the dropdown dialog in step 2
    def get_form_initial(self, step):
        returnDict = {}

        # Set default mail address (if available)
        if self.request.user.email and self.request.user.email != "":
            returnDict["notification_mail_address"] = self.request.user.email

        if step == "1":
            simulation_file = self.get_cleaned_data_for_step("0")["simulation_file"]
            omnetppini = simulation_file.read().decode("utf-8")
            simulation_file.seek(0)
            config = configparser.ConfigParser()
            config.read_string(omnetppini)
            sections = config.sections()
            # Remove HTML etc. -> XSS
            sections = [strip_tags(section) for section in sections]
            returnDict["sections"] = sections

        return self.initial_dict.get(step, returnDict)

    # Add additional template information like the title
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({"title" : "Create a new simulation: Step " + str(self.steps.step1)})
        data_1 = self.get_cleaned_data_for_step("0")
        if data_1 != None:
            context.update({"simulation_title" : data_1["simulation_title"]})
        return context

    # Form is finished, process the data, start the job
    def done(self, form_list, **kwargs):
        cleaned_data = self.get_all_cleaned_data()
        q = Queue(connection=get_redis_conn())
#        print(cleaned_data)
#        print("User", self.request.user)
#        print("Simulation title", cleaned_data["simulation_title"])
#        print("omnetpp.ini", cleaned_data["simulation_file"])
#        print("simulation name", cleaned_data["simulation_name"])
        omnetppini = cleaned_data["simulation_file"].read().decode("utf-8")

        notification_mail_address = None
        if cleaned_data["notification_mail_address"] not in ["", None]:
            notification_mail_address = cleaned_data["notification_mail_address"]

        # Handle backend
        storage_backend_id = int(cleaned_data["storage_backend"])

        # TODO: Do further checks on backend id?
        storage_backend_object = get_object_or_404(
                StorageBackend.objects.filter(backend_active=True),
                pk=storage_backend_id
                )

        args = {
                "user" : str(self.request.user),
                "title" : str(cleaned_data["simulation_title"]),
                "is_debug_sim" : str(cleaned_data["is_debug_sim"]),
                "omnetpp.ini" : str(omnetppini),
                "runconfig" : str(cleaned_data["simulation_name"]),
                "summarizing_precision" : float(cleaned_data["summarizing_precision"]),
                "storage_backend" : str(storage_backend_object.backend_name),
                "storage_backend_id" : str(storage_backend_object.backend_identifier),
                "storage_backend_token" : str(storage_backend_object.backend_token),
                "storage_backend_keep_days" : str(storage_backend_object.backend_keep_days),
                }


        print("Simulation arguments:", args)


        # Start job
        job = q.enqueue(
                run_simulation,
                SimulationRuntimes.OPS_KEETCHI,
                args,
                job_timeout=ConfigKeyValueStorage.config.get_value("DEFAULT_SIMULATION_TIMEOUT"),
                )
        print("Job with id", job.id, "started")

        # Store simulation including the job id for later
        simulation = Simulation(
                user = self.request.user,
                title = str(cleaned_data["simulation_title"]),
                simulation_is_debug_sim = cleaned_data["is_debug_sim"],
                omnetppini = str(omnetppini),
                runconfig = str(cleaned_data["simulation_name"]),
                simulation_id = job.id,
                summarizing_precision = float(cleaned_data["summarizing_precision"]),
                notification_mail_address = notification_mail_address,
                storage_backend = storage_backend_object,
                simulation_timeout = job.timeout,
                )

        simulation.save()

        # Make sure the simulation status in the db is up to date
        sync_simulations()

        # Redirect to detail view for simulation
        return redirect(simulation.get_absolute_url())



## Start a new simulation using the form wizard module
#
# view is created directly in the urls.py
class BenchSimWizard(SessionWizardView):

    template_name = 'omnetppManager/bench_simulation.html'

    # Get the sections from the omnetpp.ini for the dropdown dialog in step 2
    # Get the sections from the omnetpp.ini for the dropdown dialog in step 2
    def get_form_initial(self, step):
        returnDict = {}

        if self.request.user.email and self.request.user.email != "":
            returnDict["notification_mail_address"] = self.request.user.email


        if step == "1":
            # datax=self.storage.get_step_data('2')
            # print(datax)
            section_name = self.get_cleaned_data_for_step("0")["simulation_name"]
            returnDict["section_name"] = section_name

        if step == "2":
            # self.storage.set_step_data('2',{})
            forwarder = self.get_cleaned_data_for_step("1")["forwarding_layer"]
            returnDict["forwarder"] = forwarder
        if step == "3":
            dataz=self.storage.get_step_data('2')
            # print(step)
        return self.initial_dict.get(step, returnDict)
  
    # Add additional template information like the title
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({"title" : "Create a new simulation: Step " + str(self.steps.step1)})
        data_1 = self.get_cleaned_data_for_step("0")
        if data_1 != None:
            context.update({"simulation_title" : data_1["simulation_title"]})
            context.update({"simulation_name" : data_1["simulation_name"]})
        if self.steps.current == '2':
            # print(context["simulation_name"])
            data_2 = self.get_cleaned_data_for_step("1")
            context.update({"forwarding_layer" : data_2["forwarding_layer"]})
            # stay_step = self.request.POST.get('wizard_stay_step', None)
        
        return context
        

    # Form is finished, process the data, start the job
    def done(self, form_list, **kwargs):
        cleaned_data = self.get_all_cleaned_data()
        # print(cleaned_data)
        ini_file='\n'
        config_name=cleaned_data['simulation_name']
        forwarder_name=cleaned_data['forwarding_layer']
        # print(section_name)
        config_objects=OmnetppBenchmarkConfig.objects.all()
        # print(config_objects)
        for sec in config_objects:
            # compiling General config section
            if str(sec.name) == 'General':   
                config_param=OmnetppBenchmarkParameters.objects.filter(config=sec)
                # print(config_param)
                ini_file += config_param[0].param_default_value + '\n'
                edit_params = OmnetppBenchmarkEditableParameters.objects.filter(config=sec)
                # # print(params)
                for param in edit_params:
                    ini_file += param.param_name + ' = ' 
                    if param.user_editable == True:
                        # print(cleaned_data[param] )
                        ini_file += f'{cleaned_data[param]}'  + param.param_unit + '   #' + param.param_description + '\n'
                    else:
                        ini_file += param.param_default_value + param.param_unit + '   #' + param.param_description + '\n'

            if str(sec.name) == config_name:   
                config_param=OmnetppBenchmarkParameters.objects.filter(config=sec)
                config_simname= config_param[0].param_name
                # print(config_param)
                ini_file += '\n'+ config_param[0].param_default_value + '\n'
        forward_obj=OmnetppBenchmarkForwarderConfig.objects.all()
        ini_file += '\n\n#forwarding layer parameters \n'
        ini_file += f'#{forwarder_name}  \n'
        for fwd in forward_obj:
            if str(fwd) == forwarder_name:
                fwd_params=OmnetppBenchmarkForwarderParameters.objects.filter(config=fwd)
                for fwd_param in fwd_params:
                    ini_file += fwd_param.param_name + ' = ' 
                    if fwd_param.user_editable == True:
                        ini_file += f'{cleaned_data[fwd_param]}' + fwd_param.param_unit + '   #' + fwd_param.param_description + '\n'
                    else:
                        ini_file += fwd_param.param_default_value + fwd_param.param_unit + '   #' + fwd_param.param_description + '\n'


        # print(ini_file)
        q = Queue(connection=get_redis_conn())

        notification_mail_address = None
        if cleaned_data["notification_mail_address"] not in ["", None]:
            notification_mail_address = cleaned_data["notification_mail_address"]

        # Handle backend
        storage_backend_id = int(cleaned_data["storage_backend"])

        # TODO: Do further checks on backend id?
        storage_backend_object = get_object_or_404(
                StorageBackend.objects.filter(backend_active=True),
                pk=storage_backend_id
                )

        args = {
                "user" : str(self.request.user),
                "title" : str(cleaned_data["simulation_title"]),
                "omnetpp.ini" : str(ini_file),
                "runconfig" : str(config_param[0].param_name),
                "summarizing_precision" : float(cleaned_data["summarizing_precision"]),
                "storage_backend" : str(storage_backend_object.backend_name),
                "storage_backend_id" : str(storage_backend_object.backend_identifier),
                "storage_backend_token" : str(storage_backend_object.backend_token),
                "storage_backend_keep_days" : str(storage_backend_object.backend_keep_days),
                }


        # print("Simulation arguments:", args)


        # Start job
        job = q.enqueue(
                run_simulation,
                SimulationRuntimes.OPS_KEETCHI,
                args,
                job_timeout=ConfigKeyValueStorage.config.get_value("DEFAULT_SIMULATION_TIMEOUT"),
                )
        # print("Job with id", job.id, "started")

        # Store simulation including the job id for later
        simulation = Simulation(
                user = self.request.user,
                title = str(cleaned_data["simulation_title"]),
                omnetppini = str(ini_file),
                runconfig = str(config_param[0].param_name),
                simulation_id = job.id,
                summarizing_precision = float(cleaned_data["summarizing_precision"]),
                notification_mail_address = notification_mail_address,
                storage_backend = storage_backend_object,
                simulation_timeout = job.timeout,
                )

        simulation.save()

        # Make sure the simulation status in the db is up to date
        sync_simulations()

        # Redirect to detail view for simulation
        return redirect(simulation.get_absolute_url())



## Generic view: Show job information
class JobDetailView(DetailView):
    model = Simulation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Job detail view"
        return context


class DetailSimWizard(SessionWizardView):
    template_name = "omnetppManager/create_detail_sim.html"
    form_list     = [
            GeneralSettingForm,
            formset_factory(NodeSettingForm, extra=1, formset=BaseNodeSettingFormSet),
            ModelDetailSettingForm
            ]

    # Get the data from the previous sections
    def get_form_kwargs(self, step):

        returnDict = super().get_form_kwargs(step)
        returnDict = {}

        if step == "2":
            base_data = self.get_cleaned_data_for_step("0")
            data = self.get_cleaned_data_for_step("1")

            returnDict["base_sim_settings"] = base_data
            returnDict["nodes_sim_settings"] = data

        return returnDict

        # Get the sections from the omnetpp.ini for the dropdown dialog in step 2
    def get_form_initial(self, step):
        returnDict = {}

        # Set default mail address (if available)
        if self.request.user.email and self.request.user.email != "" and step=="0":
            returnDict["notification_mail_address"] = self.request.user.email
        return self.initial_dict.get(step, returnDict)

    def done(self, form_list, form_dict, **kwargs):
        cleaned_data = self.get_all_cleaned_data()

        #print([form.cleaned_data for form in form_list])
        omnetppini = createOmnetppFromForm(form_list, form_dict)

        # Get config from generated omnetpp.ini
        config = configparser.ConfigParser()
        config.read_string(omnetppini)
        sections = config.sections()
        simulation_name = "[General]" # Default to general config
        # get 1st config found
        if len(sections):
            simulation_name = sections[0]

        q = Queue(connection=get_redis_conn())

        notification_mail_address = None
        if cleaned_data["notification_mail_address"] not in ["", None]:
            notification_mail_address = cleaned_data["notification_mail_address"]

        # Handle backend
        storage_backend_id = int(cleaned_data["storage_backend"])

        # TODO: Do further checks on backend id?
        storage_backend_object = get_object_or_404(
                StorageBackend.objects.filter(backend_active=True),
                pk=storage_backend_id
                )

        args = {
                "user" : str(self.request.user),
                "title" : str(cleaned_data["simulation_title"]),
                "omnetpp.ini" : str(omnetppini),
                "runconfig" : str(simulation_name),
                "summarizing_precision" : float(cleaned_data["summarizing_precision"]),
                "storage_backend" : str(storage_backend_object.backend_name),
                "storage_backend_id" : str(storage_backend_object.backend_identifier),
                "storage_backend_token" : str(storage_backend_object.backend_token),
                "storage_backend_keep_days" : str(storage_backend_object.backend_keep_days),
                }


        print("Simulation arguments:", args)


        # Start job
        job = q.enqueue(
                run_simulation,
                SimulationRuntimes.OPS_KEETCHI,
                args,
                job_timeout=ConfigKeyValueStorage.config.get_value("DEFAULT_SIMULATION_TIMEOUT"),
                )
        print("Job with id", job.id, "started")

        # Store simulation including the job id for later
        simulation = Simulation(
                user = self.request.user,
                title = str(cleaned_data["simulation_title"]),
                omnetppini = str(omnetppini),
                runconfig = str(simulation_name),
                simulation_id = job.id,
                summarizing_precision = float(cleaned_data["summarizing_precision"]),
                notification_mail_address = notification_mail_address,
                storage_backend = storage_backend_object,
                simulation_timeout = job.timeout,
                )

        simulation.save()

        # Make sure the simulation status in the db is up to date
        sync_simulations()

        # Redirect to detail view for simulation
        return redirect(simulation.get_absolute_url())



    # Add additional template information like the title
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({"title" : "Create a new simulation: Step " + str(self.steps.step1)})
        return context

## helper

## Update the status in the simulation db.
#
# Returns true, if something was updated
def update_sim_status(simulation_id, new_status, terminate_reason=Simulation.TerminateReason.NOT_TERMINATED):
    if new_status == Simulation.Status.ABORTED and terminate_reason==Simulation.TerminateReason.NOT_TERMINATED:
        raise ValueError("If you abort a simulation, you have to give a terminate reason.")
    if new_status != Simulation.Status.ABORTED and terminate_reason != Simulation.TerminateReason.NOT_TERMINATED:
        raise ValueError("If a simulation is aborted, a terminate reason has to be given.")

    sim = None
    try:
        sim = Simulation.objects.get(simulation_id=simulation_id)
        if sim.status != new_status:
            sim.status = new_status
            state_time = timezone.now()
            sim.simulation_last_update_time = state_time
            sim.terminated = terminate_reason
            sim.save()
            sim.add_state_times(sim.get_status_display(), state_time)
            if sim.send_notify_mail():
                # Send status update mail
                userMessage = "The status of your simulation with the id " + str(simulation_id) + " has changed. New status: " + str(sim.get_status_display())

                if sim.is_finished() and sim.get_shared_link():
                    userMessage += "\n\nYou can download the results here: " + str(sim.get_shared_link())

                send_mail(
                        "Simulation status update",
                        userMessage,
                        ConfigKeyValueStorage.config.get_value("DEFAULT_SENDER_MAIL_ADDRESS"),
                        [sim.notification_mail_address, ],
                        fail_silently = False,
                        )
            return True
    except Simulation.DoesNotExist:
        print("Sim does not exists in db", simulation_id, new_status)
        sim = None

    return False

## Store results
#
# Returns true, if something was updated
def store_sim_results(simulation_id, meta, data=None, job_error=None, job=None):
    sim = None
    try:
        sim = Simulation.objects.get(simulation_id=simulation_id)

        if job:
            sim.simulation_start_time = job.started_at.replace(tzinfo=pytz.UTC)

        if job_error != None:
            sim.job_error = str(job_error)

        if "exception" in meta:
            sim.simulation_error = meta["exception"]

        if "handled_by" in meta:
            sim.handled_by = meta["handled_by"]

        if data != None:
            if isinstance(data, dict):
                print(data)
                if "shared_link" in data and data["shared_link"] and data["shared_link"] != "":
                    sim.shared_link = data["shared_link"]
                    print("Stored shared link")

        if len(meta):
            # Do not store empty meta data
            try:
                sim.meta_full = json.dumps(meta)
            except:
                sim.meta_full = meta

        sim.save()
        return True
    except Simulation.DoesNotExist:
        print("Simulation does not exist")
        sim = None
    return False


# Return a valid redis connection
def get_redis_conn():
    host = ConfigKeyValueStorage.config.get_value("REDIS_DB_HOST", "localhost")
    port = ConfigKeyValueStorage.config.get_value("REDIS_DB_PORT", 6379)
    password = ConfigKeyValueStorage.config.get_value("REDIS_DB_PASSWORD", None)

    return Redis(host=host, port=port, password=password)


# Sync sim status with queue / sim database
def sync_simulations(redis_conn=get_redis_conn()):
    q = Queue(connection=get_redis_conn())

    finished_jobs = len(q.finished_job_registry)
    failed_jobs = len(q.failed_job_registry)

    updated_jobs = 0

    for j in q.finished_job_registry.get_job_ids():
        job = q.fetch_job(j)
        store_sim_results(j, job.meta, job.result, job.exc_info, job=job)
        q.finished_job_registry.remove(job)

        update_sim_status(j, Simulation.Status.FINISHED)

    for j in q.failed_job_registry.get_job_ids():
        job = q.fetch_job(j)

        store_sim_results(j, job.meta, job.result, job.exc_info, job=job)
        q.failed_job_registry.remove(job)

        update_sim_status(j, Simulation.Status.FAILED)

    # update job status

    for j in q.get_job_ids():
        if update_sim_status(j, Simulation.Status.QUEUED):
            updated_jobs += 1

    for j in q.started_job_registry.get_job_ids():
        if update_sim_status(j, Simulation.Status.STARTED):
            updated_jobs += 1
        # update meta
        store_sim_results(j, q.fetch_job(j).meta, job=q.fetch_job(j))

    for j in q.deferred_job_registry.get_job_ids():
        if update_sim_status(j, Simulation.Status.DEFERRED):
            updated_jobs += 1

    for j in q.scheduled_job_registry.get_job_ids():
        if update_sim_status(j, Simulation.Status.SCHEDULED):
            updated_jobs += 1


    return {
                "failed_jobs" : failed_jobs,
                "finished_jobs" : finished_jobs,
                "updated_jobs" : updated_jobs,
            }

# Sim helper

# Create a valid omnetpp.ini from the form data
# TODO: Evaluate?
def createOmnetppFromForm(form_list, form_dict):
    form_out = "[General]\n"

    for form in form_list:
        if isinstance(form, ModelDetailSettingForm):
            fields = form.get_fields()
            for field in fields:
                form_out += str(field) + " = " + str(fields[field]) + "\n"

        elif hasattr(form, "__len__") and len(form)>0 and isinstance(form[0], NodeSettingForm):
            for f in form:
                print(f.get_fields())

        elif isinstance(form, GeneralSettingForm):
            print(form.get_fields())
        else:
            print("not impl")

            #print(form_dict)
            #print("CLEANED", form.cleaned_data)
    return form_out


## Server config access

def get_server_config(request):
    server_token = request.headers.get("HTTP-X-HEADER-TOKEN")
    server_id = request.headers.get("HTTP-X-HEADER-SERVER-ID")

    json_response = {}

    # Check for the headers
    server = ServerConfig.objects.filter(server_token=server_token, server_id=server_id)
    if len(server) == 1:
        print("HERE")
        config = ServerConfigValue.objects.filter(server=server[0]).values("key", "value")
        json_response[server.first().server_id] = list(config)

    # No auth headers -> is user logged in?
    elif request.user.is_authenticated:
        for server in ServerConfig.objects.all():
            config = ServerConfigValue.objects.filter(server=server).values("key", "value")
            json_response[server.server_id] = list(config)

    # If nothing fits: empty json object
    return JsonResponse(json_response)
