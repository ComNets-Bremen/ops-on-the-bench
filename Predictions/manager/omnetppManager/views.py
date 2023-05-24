from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.utils.html import strip_tags, format_html
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import Group, User
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .decorators import already_authenticated, auth_required
from django.forms import formset_factory
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.utils.datastructures import MultiValueDict

from django.core.mail import send_mail

from formtools.wizard.views import SessionWizardView

from .models import Simulation, StorageBackend, ConfigKeyValueStorage, ServerConfig, ServerConfigValue,\
     OmnetppBenchmarkConfig, OmnetppBenchmarkParameters, OmnetppBenchmarkEditableParameters, OmnetppBenchmarkForwarderConfig, OmnetppBenchmarkForwarderParameters,\
         UserProfile, UserProfileParameters

from .forms import getOmnetppiniForm, selectSimulationForm,getOmnetppBenchmarkSection,selectForwarderForm, BenchmarkGeneralSettingForm,UserEditorForm

from rq import Queue
from rq.job import Job
from redis import Redis
from rq.command import send_stop_job_command
from rq.serializers import DefaultSerializer,JSONSerializer

import configparser

import io

import json

import os, re
from django.core.exceptions import SuspiciousOperation

import datetime, time, random
import pytz


import numpy as np
import pandas as pd
from scipy.special import boxcox1p,inv_boxcox1p
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
#from keras.layers import LeakyReLU
#from keras.losses import mean_squared_error,mean_absolute_error,huber_loss
from sklearn.ensemble import GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb
from sklearn.base import BaseEstimator, TransformerMixin,RegressorMixin,clone
#LeakyReLU = LeakyReLU(alpha=0.1)
import pickle
import warnings
import requests
warnings.filterwarnings('ignore')




from .forms import getOmnetppiniForm, selectSimulationForm, NodeSettingForm, GeneralSettingForm, ModelDetailSettingForm, BaseNodeSettingFormSet, RequestAccessForm, RerunSimForm,\
    CreateUsers, ModelPredictionForm

from utils.worker import run_simulation, SimulationRuntimes



# Create your views here.

## Redirect app from / -> /omnetppManager
def redirect_to_here(request):
    return HttpResponseRedirect(reverse("omnetppManager_index"))

## Index page
def index(request):
    return render(request, 'omnetppManager/index.html', {'title':"Overview"})

## it has been depreciated, since registration view is up now
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

## it has been depreciated, since registration view is up now
def request_access_thanks(request):
    return render(request, 'omnetppManager/request_access_thanks.html', {'title': "Thanks for your request"})

## User registration
@already_authenticated
def register_users(request):
    form = CreateUsers()
    
    if request.method == 'POST':
        form = CreateUsers(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            username = form.cleaned_data.get('username')
            current_site = get_current_site(request)
            mail_subject = 'Activate your OOTB account.'
            message = render_to_string('registration/user_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            send_mail(
                        mail_subject,
                        message,
                        ConfigKeyValueStorage.config.get_value("DEFAULT_SENDER_MAIL_ADDRESS"),
                        [to_email, ],
                        fail_silently = False,
                        )
            
            messages.info(request, f'{username} please confirm your email address to complete the registration !')
            return redirect('omnetppManager_login')
    context= {'form': form}
    return render(request,'registration/register_users.html', context)


## User registration
@already_authenticated
def resend_activation(request):
    if request.method == 'POST':
        email_address = request.POST.get('email')
        for user in User.objects.all():
            if str(user.email) == email_address:
                current_site = get_current_site(request)
                mail_subject = 'Activate your OOTB account.'
                message = render_to_string('registration/user_activation_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                    'token':account_activation_token.make_token(user),
                })
                to_email = email_address
                send_mail(
                            mail_subject,
                            message,
                            ConfigKeyValueStorage.config.get_value("DEFAULT_SENDER_MAIL_ADDRESS"),
                            [to_email, ],
                            fail_silently = False,
                            )
                
        messages.info(request, f'if the a valid email address was used you will receive a mail, please confirm your email address to complete the registration !')
        return redirect('omnetppManager_login')
    return render(request, 'registration/resend_activation.html')


## activate user after confirmationx`
def activate_account(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        group, created = Group.objects.get_or_create(name='Simple User')
        user.groups.add(group)
        user.save()
        messages.success(request, 'Account successfully activated for ' + user.username)
        return redirect('omnetppManager_login')
        # return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')


## User login
@already_authenticated
def login_users(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username = username, password = password)

        if user != None:
            # add groups to already exiting users without user profiles
            group_simple, created = Group.objects.get_or_create(name='Simple User')
            group_staff, created1 = Group.objects.get_or_create(name='Staff User')
            if len(Group.objects.filter(user = user)) == 0:
                if user.is_staff:
                    user.groups.add(group_staff)
                else:
                    user.groups.add(group_simple)
            # add is active logic here
            if user.is_active:
                login(request, user)
                return redirect('omnetppManager_index')
        else:
            for name in User.objects.all():
                if str(name) == username:
                    if name.is_active:
                        messages.info(request,'username or password is incorrect, try again!')
                    else:
                        messages.info(request, format_html('user not activated yet, activate your account! or <a href="{}">resend activation link</a>', reverse('resend_activation')))
    return render(request, 'registration/login.html')


## User logout
def logout_users(request):
    logout(request)
    return redirect('omnetppManager_login')

## change password view
@auth_required
def change_password(request):
    user= request.user
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
    user= request.user

    q = Queue(connection=get_redis_conn())
    
    # for simple user view
    if not user.is_superuser:
        simulations = Simulation.objects.filter(user = user)
        queued_jobs = q.get_job_ids()
        user_queue, finished, started, deferred, scheduled, aborted, failed = [0]*7
        for sim_id in simulations:
            if str(sim_id.simulation_id) in queued_jobs:
                user_queue += 1
            if sim_id.status == 2:
                finished += 1
            if sim_id.status == 3:
                failed += 1
            if sim_id.status == 8:
                aborted += 1
            if sim_id.status == 4:
                started += 1
            if sim_id.status == 5:
                deferred += 1
            if sim_id.status == 6:
                scheduled += 1
        status.append([{
            "name" : "Queued jobs",
            "number" : user_queue,
            },
            {
            "name" : "Finished jobs",
            "number" : finished,
            },
            {
            "name" : "Started jobs",
            "number" : started,
            },
            {
            "name" : "Deferred jobs",
            "number" : deferred,
            },
            {
            "name" : "Scheduled jobs",
            "number" : scheduled,
            },
            {
            "name" : "Aborted jobs",
            "number" : aborted,
            },
            {
            "name" : "Failed jobs",
            "number" : failed,
            }]
            )
        print(status)
    # for admin view     
    else:
        simulations = Simulation.objects.all()
        finished, aborted, failed = [0]*3
        for sims in simulations:
            if sims.status == 2:
                finished += 1
            if sims.status == 3:
                failed += 1
            if sims.status == 8:
                aborted += 1
        status.append([{
            "name" : "Queued jobs",
            "number" : len(q),
            },
            {
            "name" : "Finished jobs",
            "number" : finished,
            },
            {
            "name" : "Started jobs",
            "number" : len(q.started_job_registry),
            },
            {
            "name" : "Deferred jobs",
            "number" : len(q.deferred_job_registry),
            },
            {
            "name" : "Scheduled jobs",
            "number" : len(q.scheduled_job_registry),
            },
            {
            "name" : "Aborted jobs",
            "number" : aborted,
            },
            {
            "name" : "Failed jobs",
            "number" : failed,
            }])

    return render(request, 'omnetppManager/queue_status_page.html', {
            "status" : status[0],
            "title"  : "Queue status",
        })

## Show status of jobs
@login_required
def job_status(request):
    user= request.user
    if not user.is_superuser:
        simulations = Simulation.objects.filter(user = user)
        paginator = Paginator(simulations, 25) # 25 items per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, "omnetppManager/job_status_page.html",
                {
                    "jobs" : page_obj,
                    "title" : "Job status",
                })
    else:
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

    sync_simulations2()
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
    connection=get_redis_conn()
    running_jobs=q.started_job_registry.get_job_ids()
    # queued_jobs =q.get_job_ids()
    # failed = q.failed_job_registry.get_job_ids()

    # for diagonising job status
    # print('running', len(running_jobs))
    # print('que', len(queued_jobs))
    # print('failed', list(failed))
    job = Job.fetch(str(simulation.simulation_id), connection=connection)
    job_status=job.get_status()

    if q.remove(str(simulation.simulation_id)) > 0:
        # We removed one job. update status:
        update_sim_status(
                simulation.simulation_id,
                Simulation.Status.ABORTED,
                Simulation.TerminateReason.TERMINATED_USER
                )
        
    elif str(simulation.simulation_id) in running_jobs: 
        # trys to stop running job and update status
        send_stop_job_command(connection, str(simulation.simulation_id))
        # update sim status

        update_sim_status(
                simulation.simulation_id,
                Simulation.Status.ABORTED,
                Simulation.TerminateReason.TERMINATED_USER
                )
    else:
        print("Not able to remove simulation from queue", len(q), "or started registry" )

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
                
            ## choose server
            servers = list(ServerConfig.objects.all())
            server = random.choice(servers)

            args = {
                    "user" : str(request.user),
                    "title" : str(form.cleaned_data["simulation_title"]),
                    "omnetpp.ini" : str(simulation.omnetppini),
                    "runconfig" : str(simulation.runconfig),
                    "summarizing_precision" : float(simulation.summarizing_precision),
                    "storage_backend" : str(simulation.storage_backend.backend_name),
                    "storage_backend_id" : str(simulation.storage_backend.backend_identifier),
                    "storage_backend_token" : str(simulation.storage_backend.backend_token),
                    "storage_backend_config" : str(simulation.storage_backend.backend_config) if hasattr(simulation.storage_backend, "backend_config") else "",
                    "storage_backend_keep_days" : str(simulation.storage_backend.backend_keep_days),
                    "server" : str(server),
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
            simulation.sim_server = str(server)

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

    Gomnetppini = ""
    Grunconfig = ""
    
    # change post function to accomodate handling of multiple ini files
    def post(self, *args, **kwargs):
        form = self.get_form(data=self.request.POST, files=self.request.FILES)
        if form.is_valid():
            self.storage.set_step_data(self.steps.current, self.process_step(form))
            # apply changes to only step 0
            if self.steps.current == '0':
                files=self.request.FILES.getlist('0-simulation_file')
                # overwrite file saving method to temporary save each files using file name
                for f in files:
                    if f == files[0]:
                        file= MultiValueDict({f'0-simulation_file': [f]})
                    else:
                        file= MultiValueDict({f'0-simulation_file{f}': [f]})
                    # file= {f'0-simulation_file_{f}': [files[0],files[1]]}
                    form1 = self.get_form(data=self.request.POST, files=file)
                    form.is_valid()
                    # print('0', files, '\n', len(files), '\n',files['0-simulation_file'],'\n', len(files['0-simulation_file']))
                    self.storage.set_step_files(self.steps.current, self.process_step_files(form1))
                # print('2', self.storage.current_step_files)
                # print('3',self.storage.current_step_data)
                return self.render_next_step(form)
            else: 
                self.storage.set_step_files(self.steps.current, self.process_step_files(form))
                # check if the current step is the last step
                if self.steps.current == self.steps.last:
                    # no more steps, render done view
                    return self.render_done(form, **kwargs)
                else:
                    # proceed to the next step
                    return self.render_next_step(form)
        return self.render(form)


    # Get the sections from the omnetpp.ini for the dropdown dialog in step 2
    def get_form_initial(self, step):
        returnDict = {}

        # Set default mail address (if available)
        if self.request.user.email and self.request.user.email != "":
            returnDict["notification_mail_address"] = self.request.user.email
        # Use the first file to setup config parameters and sections 
        if step == "1":
            simulation_file = self.get_cleaned_data_for_step("0")["simulation_file"]
            omnetppini = simulation_file.read().decode("utf-8")
            simulation_file.seek(0)
            config = configparser.ConfigParser()
            config.read_string(omnetppini)
            sections = config.sections()
            self.Gomnetppini = str(omnetppini)
            # Remove HTML etc. -> XSS
            sections = [strip_tags(section) for section in sections]
            returnDict["sections"] = sections
            
        elif step == "2":
            print("THE OMNETPP FILE IS AS FOLLOWS : ",self.Gomnetppini)
            simulation_name = self.get_cleaned_data_for_step("1")["simulation_name"]
            print('Simulation name is : ', simulation_name)
            predictions = self.predict(self.Gomnetppini,str(simulation_name))
            #predictions = [10000,20000,30000,40]

            returnDict["peak_disk_usage"] = str(round(predictions[0]*1e-9,2))+" GB"
            returnDict["peak_RAM_usage_simulation"] = str(round(predictions[1]*1e-9,2))+" GB"
            returnDict["peak_RAM_usage_results"] = str(round(predictions[2]*1e-9,2))+" GB"
            returnDict["total_time_taken"] = str(round(predictions[3],2))+" Seconds"

        return self.initial_dict.get(step, returnDict)

    # Add additional template information like the title
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context.update({"title" : "Create a new simulation: Step " + str(self.steps.step1)})
        data_1 = self.get_cleaned_data_for_step("0")
        
        if data_1 != None:
            print(data_1)
            context.update({"simulation_title" : data_1["simulation_title"]})
        
        if self.steps.step1 == 3:       
        #    r_temp = get_redis_conn()       
        #    try:
            url2 = "http://192.168.142.128:8000/omnetppManager/get-server-config/"
    
            headers = {'HTTP-X-HEADER-SERVER-ID':'uranus', 'HTTP-X-HEADER-TOKEN':'8103487f-9eb4-49e8-918d-a3d31bad2020'}
					
            response2 = requests.get(url2,headers=headers)
    
            if response2.status_code == 200:
                servdata = response2.json()
                #print(type(servdata))
            else:
                print("No Server Content was read")
                
            dicts = {}
            for key,value in servdata.items():
                max_ram = 0
                max_disk = 0
                
                disk = {}
                li = []
            
                for dic in value:
                    for k,v in dic.items():
                        li.append(v)
                    
                for i in range(len(li)):
                    if li[i]=='max_ram':
                        max_ram = li[i+1]
                    elif li[i]=='max_disk_space':
                        max_disk = li[i+1]
                    
                    disk['max_ram'] = max_ram
                    disk['max_disk_space'] = max_disk
                    dicts[key] = disk
                    
            for key,value in dicts.items():
                server = key
                Tm = int(value['max_ram'])
                Tds = int(value['max_disk_space'])
                break
                
            Tm = Tm*1e-9
            Tds = Tds*1e-9
                
        #        server_contents = r_temp.lrange('server_resource', 0, -1)
        #        server_dict = [json.loads(json_dict) for json_dict in server_contents]           
        #        Tds = server_dict[0]["Total_Disk_Space"]
        #        Tm = server_dict[0]["Total_Memory"]/1024
            context.update({"Total_Server_Resources":str(round(Tds,2))+" GB of Disk"+" and "+str(round(Tm,2))+" GB of RAM"})
            
            run_name = self.get_cleaned_data_for_step("1")["simulation_name"]
            preds = self.predict(self.Gomnetppini,str(run_name))
            
            pred_disk = round(preds[0]*1e-9,2)
            pred_ram = max(round(preds[1]*1e-9,2),round(preds[2]*1e-9,2))
            
            if pred_disk>=Tds or pred_ram>=Tm:
                context.update({"recommendation":"Resources required by the simulation exceeds maximum server resources. Reconfigure."})
            elif pred_disk>Tds*0.9 or pred_ram>Tm*0.9:
                context.update({"recommendation":"Resources required by the simulation use 90% of maximum server resources. Try to Reconfigure."})
            else:
                context.update({"recommendation":"Resources required are less than maximum server resources."})
        #    except:
        #        context.update({"Total_Server_Resources":"No Data Available"})
        #    r_temp.close()         
               
            data_2 = self.get_cleaned_data_for_step("1")
            if data_2 != None:
                context.update({"simulation_name" : data_2["simulation_name"]})                
        return context

    # Form is finished, process the data, start the job
    def done(self, form_list, **kwargs):
        cleaned_data = self.get_all_cleaned_data()
        files =  self.storage.get_step_files(self.steps.first)
        # process each files starting with the first file in the cleaned data and the remaining files in temporary storage
        for file in files:
            if files[file] == cleaned_data["simulation_file"]:
                omnetppini = cleaned_data["simulation_file"].read().decode("utf-8")
                runconfig = str(cleaned_data["simulation_name"])
                # print('try1',cleaned_data["simulation_file"])
            else:
                omnetppini = files[file].read().decode("utf-8")
                runconfig = str(cleaned_data["simulation_name"])
            
            #print("Inside Done",omnetppini,runconfig)    
            predictions = self.predict(omnetppini,runconfig)
            
            r = get_redis_conn()
            #q = Queue(connection=r)
            q = Queue('secondary', connection=r)

            # print(cleaned_data)
            # print("User", self.request.user)
            # print("Simulation title", cleaned_data["simulation_title"])
            # print("omnetpp.ini", cleaned_data["simulation_file"])
            # print("simulation name", cleaned_data["simulation_name"])
                
            # omnetppini = cleaned_data["simulation_file"].read().decode("utf-8")

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
            servers = list(ServerConfig.objects.all())
            server = random.choice(servers)

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
                    "storage_backend_config" : str(storage_backend_object.backend_config),
                    "server" : str(server),
                    
                    }
            # print("Simulation arguments:", args)

            #con = get_redis_conn()
            #if con.get("Total_Disk_Space") is not None:
            #    print("RETRIEVING DISK SPACE from redis : ",con.get("Total_Disk_Space"))
            #else:
            #    print("KEY doesn't exist yet")
                 
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
                    simulation_is_debug_sim = cleaned_data["is_debug_sim"],
                    omnetppini = str(omnetppini),
                    runconfig = str(cleaned_data["simulation_name"]),
                    simulation_id = job.id,
                    summarizing_precision = float(cleaned_data["summarizing_precision"]),
                    notification_mail_address = notification_mail_address,
                    storage_backend = storage_backend_object,
                    simulation_timeout = job.timeout,
                    sim_server = str(server),
                    Predicted_DiskSpace = round(predictions[0]*1e-9,2),
                    Predicted_RAM_Sim = round(predictions[1]*1e-9,2),
                    Predicted_RAM_Res = round(predictions[2]*1e-9,2),
                    Predicted_Time = round(predictions[3],2),
                    )
                    
            #pred_dict = {"simulation_id" : job.id,
            		#"pred_peak_disk_usage" : round(predictions[0]*1e-9,2),
                    #"pred_peak_RAM_simulation" : round(predictions[1]*1e-9,2),
                    #"pred_peak_RAM_results" : round(predictions[2]*1e-9,2),
                    #"pred_time_taken" : round(predictions[3],2)}
            
            
            #pred_dict_str = json.dumps(pred_dict)
            
            #r.rpush('preds_queue', pred_dict_str)

            simulation.save()

            # Make sure the simulation status in the db is up to date
            sync_simulations2()
            sync_simulations()	
        # Redirect to detail view for simulation
        return redirect(simulation.get_absolute_url())
        #return HttpResponse("Predictions are made")
    
    def predict(self,Gomnetppini,Grunconfig):
        print("Inside Predictsssssss")
        configs = configparser.ConfigParser()
        
        configs.read_string(Gomnetppini)
        
        items = configs.items(Grunconfig)
        
        dictParams = {}
        for key,value in items:
            k = key.replace('**.','')
            v = value.replace('"','')
            if '#' in v:
                v = v.split('#')[0].strip()
            dictParams[k] = v
    
        #omnet = re.compile(Grunconfig + r'[\]\n\#\s\w\*\.=\(\)\"\,\-\/]+').findall(Gomnetppini)
        #allParams = re.findall(r'\*\*\.([a-zA-Z\.]+) = ([A-Za-z0-9\"\.\/\-]+)',str(omnet))
        #dictParams = dict(allParams)
        
        df1 = pd.DataFrame(dictParams,index=[0])
        df1.columns = df1.columns.str.replace('.','_',regex=False)
        #print(df1.head())
        
        Numericals = ['app_datagenerationinterval','numnodes','app_datasizeinbytes']
        
        Categoricals = ['applicationlayer','forwardinglayer','linklayer']
        
        SWIMs = ['constraintareamaxx','constraintareamaxy','mobility_nooflocations','mobility_hosts', 'mobility_speed']
        
        try:
            if 'mobilitytype' in dictParams:
            
                if df1['mobilitytype'].values[0] == "BonnMotionMobility":
                    print("BONN")
                    df = pd.concat([df1[Numericals],df1[Categoricals]],axis=1)
                    df['constraintareamaxx'] = "0m"
                    df['constraintareamaxy'] = "0m"
                    df['mobility_nooflocations'] = 0
                    df['mobility_hosts'] = 0
                    df['mobility_speed'] = "0mps"
                    print("BONN")
                
                elif df1['mobilitytype'].values[0] =="SWIMMobility":
                    df = pd.concat([df1[Numericals],df1[Categoricals],df1[SWIMs]],axis=1)
                    df = df.fillna('0')
                    print("SWIM")
                
            else:
                print("Trace")
                df = pd.concat([df1[Numericals],df1[Categoricals]],axis=1)
                df['constraintareamaxx'] = "0m"
                df['constraintareamaxy'] = "0m"
                df['mobility_nooflocations'] = 0
                df['mobility_hosts'] = 0
                df['mobility_speed'] = "0mps"
                print("TRACE")
                
                
            
            fwd = []
            app = []
            mob = []
            link = []
            Id = []
            
		    
		    # Converting Categoricals to OneHots
            if df['forwardinglayer'].values[0].replace('"','') == "KEpidemicRoutingLayer":
                fwd = [0,0,0,0,0]
            elif df['forwardinglayer'].values[0].replace('"','') == "KKeetchiLayer":
                fwd = [1,0,0,0,0]
            elif df['forwardinglayer'].values[0].replace('"','') == "KOptimumDelayRoutingLayer":
                fwd = [0,1,0,0,0]
            elif df['forwardinglayer'].values[0].replace('"','') == "KProphetRoutingLayer":
                fwd = [0,0,1,0,0]
            elif df['forwardinglayer'].values[0].replace('"','') == "KRRSLayer":
                fwd = [0,0,0,1,0]
		    # elif df['forwardingLayer'].values[0] == "KSpraywaitRoutingLayer":
            else:
                fwd = [0,0,0,0,1]
            print("Forwarding Selected")
            
            
		    
            if 'mobilityType' in dictParams:
                if df1['mobilitytype'].values[0].replace('"','') =="BonnMotionMobility":
                    mob = [0,0]
                elif df1['mobilitytype'].values[0].replace('"','') =="SWIMMobility":
                    mob = [1,0]
            else:
                mob = [0,1]
            print("mobility Selecetd")
            
		        
            
            if df['applicationlayer'].values[0].replace('"','') =="KHeraldApp":
                app = [0,0]
            elif df['applicationlayer'].values[0].replace('"','') =="KHeraldAppForDifferentiatedTraffic":
                app = [1,0]
            else:
                app = [0,1]
            print("Application Selected")
            
		          
		        
            if df['linklayer'].values[0].replace('"','') =="KWirelessInterface":
                link = [0]
            else:
                link = [1]
            print("Link",link)
            
		    
            if 'mobility.nodeid' in dictParams:
                Id = [1]
            else:
                Id = [0]
            
            print("Mobility node ID Selecetd")
		    
		     
		    #Preprocessing Numerical Features
            df['app_datagenerationinterval'] =  df.app_datagenerationinterval.apply(lambda x : x.replace('s','') if 's' in x else x)
            print("app_datagenerationinterval Selecetd")
            
            df['constraintareamaxx'] =  df.constraintareamaxx.apply(lambda x : x.replace('m','') if 'm' in x else x)
            print("constraintareamaxx Selecetd")
            
            df['constraintareamaxy'] =  df.constraintareamaxy.apply(lambda x : x.replace('m','') if 'm' in x else x)
            print("constraintareamaxy Selecetd")
            
            df['mobility_speed'] =  df.mobility_speed.apply(lambda x : x.replace('mps','') if 'mps' in x else x)
            print("mobility_speed Selecetd")
            
        
            def for_maxCache(cache):
                if 'bytes' in cache:
                    return cache.replace('bytes','')
                elif 'byte' in cache:
                    return cache.replace('byte','')
                else:
                    return cache
                    
            if 'forwarding_maximumcachesize' in dictParams:
                df['forwarding_maximumcachesize'] =  df1.forwarding_maximumcachesize.apply(lambda x : for_maxCache(x))
            else:
                df['forwarding_maximumcachesize'] = 0
            print("forwarding_maximumcachesize Selecetd")
            
		    
		    
		    #Preparing Input Data For Prediction
            ins1 = [float(boxcox1p(float(df.numnodes.values[0]),0.20)) , float(boxcox1p(float(df['app_datagenerationinterval'].values[0]),0.20)) , float(boxcox1p(float(df['app_datasizeinbytes'].values[0]),0.20)) ,  float(boxcox1p(float(df['forwarding_maximumcachesize'].values[0]),0.20)) ] + [float(boxcox1p(Id,0.20))]
		    
            ins2 = [float(df['constraintareamaxx'].values[0]), float(df['constraintareamaxy'].values[0]), float(df["mobility_nooflocations"].values[0]), float(df["mobility_hosts"].values[0]),  float(boxcox1p(float(df["mobility_speed"].values[0]),0.20)) ] + app + fwd + link + mob
		    
            ins = ins1 + ins2
            insf = np.array(ins).reshape(1,-1)
            
        
		    #FOR OLD MODELs
		    #df_list = df[Numericals].apply(pd.to_numeric).values
		    #input = np.concatenate([df_list,np.array([Id + app + fwd + link + mob])],axis=1)
		    #input_df = pd.DataFrame(input)
        
            input_df = pd.DataFrame(insf)
		    
		    #bc_input = boxcox1p(input_df,0.20)
            bc_input = input_df
		    
		    # Loading Pickles
		    #fs = open(r'./omnetppManager/pickles/AveragingRegressor/CharmEstFeatureScalar.pkl','rb')
            fs = open(r'./omnetppManager/pickles/AveragingRegressor/D_FeatScalar.pkl','rb')
            fscalar = pickle.load(fs)
            fs.close()
            
            scaled_input = fscalar.transform(bc_input)
            print("Scaled Input ",scaled_input)
		    
		    
		    #mod1 = open(r'./omnetppManager/pickles/AveragingRegressor/CharmAvgReg.pkl','rb')
            mod1 = open(r'./omnetppManager/pickles/AveragingRegressor/D_AvgReg3.pkl','rb')
            model1 = pickle.load(mod1)
            mod1.close()
            print("Model Predicted")

            ts = open(r'./omnetppManager/pickles/AveragingRegressor/D_TargScalar.pkl','rb')
		    #ts = open(r'./omnetppManager/pickles/AveragingRegressor/CharmEstTargetScalar.pkl','rb')
            tscalar = pickle.load(ts)
            ts.close()
            print("Scaled Back")
        

		    # Averaging Regressor Prediction
            predictions = model1.predict(scaled_input)
		    
		    #print(type(predictions))
            print("PREDICTIONS ",predictions)
            predictions = tscalar.inverse_transform(pd.DataFrame(predictions).transpose())
		    
            predictions = np.squeeze(inv_boxcox1p(predictions,0.20))
		    
        except:
            print("General Config Selected")
            predictions = np.zeros(4) 
        
        #print(omnet)
        #print(allParams)
        #print("PREDICTIONS : ", predictions.shape)
        return predictions

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
                    if fwd_param.param_type == 2 or fwd_param.param_type == 3:
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
        ## choose server
        servers = list(ServerConfig.objects.all())
        server = random.choice(servers)

        args = {
                "user" : str(self.request.user),
                "title" : str(cleaned_data["simulation_title"]),
                "omnetpp.ini" : str(ini_file),
                "runconfig" : str(config_param[0].param_name),
                "summarizing_precision" : float(cleaned_data["summarizing_precision"]),
                "storage_backend" : str(storage_backend_object.backend_name),
                "storage_backend_id" : str(storage_backend_object.backend_identifier),
                "storage_backend_token" : str(storage_backend_object.backend_token),
                "storage_backend_config" : str(storage_backend_object.backend_config),
                "storage_backend_keep_days" : str(storage_backend_object.backend_keep_days),
                "server" : str(server),
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
                omnetppini = str(ini_file),
                runconfig = str(config_param[0].param_name),
                simulation_id = job.id,
                summarizing_precision = float(cleaned_data["summarizing_precision"]),
                notification_mail_address = notification_mail_address,
                storage_backend = storage_backend_object,
                simulation_timeout = job.timeout,
                sim_server = str(server),
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

        ## choose server
        servers = list(ServerConfig.objects.all())
        server = random.choice(servers)

        args = {
                "user" : str(self.request.user),
                "title" : str(cleaned_data["simulation_title"]),
                "omnetpp.ini" : str(omnetppini),
                "runconfig" : str(simulation_name),
                "summarizing_precision" : float(cleaned_data["summarizing_precision"]),
                "storage_backend" : str(storage_backend_object.backend_name),
                "storage_backend_id" : str(storage_backend_object.backend_identifier),
                "storage_backend_token" : str(storage_backend_object.backend_token),
                "storage_backend_config" : str(storage_backend_object.backend_config),
                "storage_backend_keep_days" : str(storage_backend_object.backend_keep_days),
                "server" : str(server),
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
                sim_server = str(server),
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
    # contradicts (failed status) caused by server termiations. commenting it for now 
    # if new_status != Simulation.Status.ABORTED and terminate_reason != Simulation.TerminateReason.NOT_TERMINATED:
    #     raise ValueError("If a simulation is aborted, a terminate reason has to be given.")

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
            # The simulation job exceeded the maximum time limit
            # The simulation job exceeded the maximum disk space limit
            # The simulation exceeded the maximum RAM limit
            # The results parsing exceeded the maximum RAM limit 

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
    #print("Sync")
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
        try:
            sim = Simulation.objects.get(simulation_id=j)
            # do not update aborted sim to failed
            if sim.status == 8:
                pass
            else:
                # check if simulation was terminated by the server
                sim.terminated = 1 #NOT_TERMINATED
                server_termination_reasons = ["The simulation job exceeded the maximum time limit", "The simulation job exceeded the maximum disk space limit",
                "The simulation exceeded the maximum RAM limit", "The results parsing exceeded the maximum RAM limit"]
                for reason in server_termination_reasons:
                    if reason in sim.simulation_error:
                        if reason == server_termination_reasons[0]:
                            sim.terminated = 3 #TERMINATED_EVENTS
                        elif reason == server_termination_reasons[1]:
                            sim.terminated = 6 #TERMINATED_DISK
                        else:
                            sim.terminated = 5 #TERMINATED_RAM
                update_sim_status(j, Simulation.Status.FAILED, sim.terminated)
        except Simulation.DoesNotExist:
            print("Simulation does not exist")
            sim = None

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
            
# Sync sim status with queue / sim database
def sync_simulations2(redis_conn=get_redis_conn()):
    q = Queue('secondary',connection=get_redis_conn())

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
        try:
            sim = Simulation.objects.get(simulation_id=j)
            # do not update aborted sim to failed
            if sim.status == 8:
                pass
            else:
                # check if simulation was terminated by the server
                sim.terminated = 1 #NOT_TERMINATED
                server_termination_reasons = ["The simulation job exceeded the maximum time limit", "The simulation job exceeded the maximum disk space limit",
                "The simulation exceeded the maximum RAM limit", "The results parsing exceeded the maximum RAM limit"]
                for reason in server_termination_reasons:
                    if reason in sim.simulation_error:
                        if reason == server_termination_reasons[0]:
                            sim.terminated = 3 #TERMINATED_EVENTS
                        elif reason == server_termination_reasons[1]:
                            sim.terminated = 6 #TERMINATED_DISK
                        else:
                            sim.terminated = 5 #TERMINATED_RAM
                update_sim_status(j, Simulation.Status.FAILED, sim.terminated)
        except Simulation.DoesNotExist:
            print("Simulation does not exist")
            sim = None

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


## Simulations Details
def get_simulation_details(request):

    sim_token = request.headers.get("HTTP-X-HEADER-ID")
    
    json_response = {}
    
    if str(sim_token) == '123456789':

        for sim in Simulation.objects.all():
            print(str(sim))
            s = {}
            s['sim_id'] = sim.simulation_id
            sid = str(sim.simulation_id)
            s["title"] = sim.title
            s["exec_server"] = sim.handled_by
            s["simulation_server"] = sim.sim_server
            s["predicted_peak_disk"] = sim.Predicted_DiskSpace
            s["predicted_peak_RAM_Sim"] = sim.Predicted_RAM_Sim
            s["predicted_peak_RAM_Res"] = sim.Predicted_RAM_Res
            s["predicted_total_time"] = sim.Predicted_Time
            json_response[sid] = s
            
    elif request.user.is_authenticated:
        
        for sim in Simulation.objects.all():
            print(str(sim))
            s = {}
            s['sim_id'] = sim.simulation_id
            sid = str(sim.simulation_id)
            s["title"] = sim.title
            s["exec_server"] = sim.handled_by
            s["simulation_server"] = sim.sim_server
            s["predicted_peak_disk"] = sim.Predicted_DiskSpace
            s["predicted_peak_RAM_Sim"] = sim.Predicted_RAM_Sim
            s["predicted_peak_RAM_Res"] = sim.Predicted_RAM_Res
            s["predicted_total_time"] = sim.Predicted_Time
            json_response[sid] = s

    # If nothing fits: empty json object
    return JsonResponse(json_response)


## Server config access

def get_server_resources(request):
    json_response = {}

    for server in ServerConfig.objects.all():
        config = ServerConfigValue.objects.filter(server=server).values("key", "value")
        
        disk = {}
        li = []
        for dic in list(config):      
            for k,v in dic.items():
                #print(v)
                li.append(v)
                
        max_ram = 0
        max_disk = 0
            
        for i in range(len(li)):
            if li[i]=='max_ram':
                max_ram = li[i+1]
            elif li[i]=='max_disk_space':
                max_disk = li[i+1]
            
        disk['max_ram'] = max_ram
        disk['max_disk_space'] = max_disk
        #print(disk)
            
        json_response[server.server_id] = disk
    # If nothing fits: empty json object
    return JsonResponse(json_response)


## Server config access

def get_server_config(request):
    server_token = request.headers.get("HTTP-X-HEADER-TOKEN")
    server_id = request.headers.get("HTTP-X-HEADER-SERVER-ID")
    #print("==========",server_token)
    json_response = {}

    # Check for the headers
    server = ServerConfig.objects.filter(server_token=server_token, server_id=server_id)
    if len(server) == 1:
        # print(server)
        config = ServerConfigValue.objects.filter(server=server[0]).values("key", "value")
        json_response[server.first().server_id] = list(config)

    # No auth headers -> is user logged in?
    elif request.user.is_authenticated:
        for server in ServerConfig.objects.all():
            config = ServerConfigValue.objects.filter(server=server).values("key", "value")
            json_response[server.server_id] = list(config)

    # If nothing fits: empty json object
    return JsonResponse(json_response)

## User Profile Parameters access
def get_profile_parameters(request):
    username = request.headers.get("HTTP-X-HEADER-USER")

    json_response = {}

    # Check for the headers
    user = User.objects.filter(username=username)
    if len(user) > 0:
        profile_name = Group.objects.filter(user = user[0])

        try:
            profile = UserProfile.objects.filter(group=profile_name[0])
        except:
            return HttpResponseBadRequest('User has no group')

        if len(profile) == 1:
            parameters = UserProfileParameters.objects.filter(profile=profile[0]).values("key", "value")
            json_response[str(profile[0])] = list(parameters)

    # No auth headers -> is user logged in?
    elif request.user.is_authenticated and request.user.is_staff:
        for profile in UserProfile.objects.all():
            parameters = UserProfileParameters.objects.filter(profile=profile).values("key", "value")
            json_response[str(profile)]  = list(parameters)
    
    elif request.user.is_authenticated and not request.user.is_staff:
        return redirect('omnetppManager_index')
        # return HttpResponse('redirected')
    
    elif len(user) == 0 and username:
        return HttpResponseBadRequest('user does not exist')


    # If nothing fits: empty json object
    return JsonResponse(json_response)
