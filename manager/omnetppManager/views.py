from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.utils.html import strip_tags
from django.views.generic.detail import DetailView

from django.core.mail import send_mail

from formtools.wizard.views import SessionWizardView

from .models import Simulation, StorageBackend

from rq import Queue
from redis import Redis

import configparser

import io

import os

from .forms import getOmnetppiniForm, selectSimulationForm

from utils.worker import run_simulation, SimulationRuntimes

# Create your views here.

## Redirect app from / -> /omnetppManager
def redirect_to_here(request):
    return HttpResponseRedirect(reverse("omnetppManager_index"))

## Index page
@login_required
def index(request):
    return render(request, 'omnetppManager/index.html', {})

## Show status of queues
@login_required
def queue_status(request):
    status = []

    q = Queue(connection=Redis(host="127.0.0.1"))

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
                "jobs" : page_obj
            })


## Manage the queues and get the results from the queue.
#
# No login required: Can be called from a script. Therefore, only little
# information is given
#
# TODO: Increase security?
def manage_queues(request, output_format="json"):
    redis_conn = Redis(host="127.0.0.1")
    q = Queue(connection=redis_conn)

    finished_jobs = len(q.finished_job_registry)
    failed_jobs = len(q.failed_job_registry)

    updated_jobs = 0

    for j in q.finished_job_registry.get_job_ids():
        update_sim_status(j, Simulation.Status.FINISHED)

        job = q.fetch_job(j)
        store_sim_results(j, job.meta, job.result)
        q.finished_job_registry.remove(job)


    for j in q.failed_job_registry.get_job_ids():
        update_sim_status(j, Simulation.Status.FAILED)

        job = q.fetch_job(j)
        store_sim_results(j, job.meta, job.result)
        q.failed_job_registry.remove(job)


    # update job status

    for j in q.get_job_ids():
        if update_sim_status(j, Simulation.Status.QUEUED):
            updated_jobs += 1

    for j in q.started_job_registry.get_job_ids():
        if update_sim_status(j, Simulation.Status.STARTED):
            updated_jobs += 1

    for j in q.deferred_job_registry.get_job_ids():
        if update_sim_status(j, Simulation.Status.DEFERRED):
            updated_jobs += 1

    for j in q.scheduled_job_registry.get_job_ids():
        if update_sim_status(j, Simulation.Status.SCHEDULED):
            updated_jobs += 1


    return_values = {
                "failed_jobs" : failed_jobs,
                "finished_jobs" : finished_jobs,
                "updated_jobs" : updated_jobs,
            }


    if output_format == "json":
        return JsonResponse(return_values)
    else: # http output
        return render(
            request,
            'omnetppManager/manage_queues.html',
            return_values
            )

## Kill queues sims
#
# Tries to kill a simulation. Currently only kills queued sims
# TODO: Extend, kill all kind of simulations
# TODO: Ask if it is okay to kill the sim
@login_required
@require_http_methods(["POST",])
def job_kill(request, pk):
    simulation = get_object_or_404(
            Simulation,
            pk=pk
            )
    print("Trying to kill simulation", simulation.simulation_id)

    redis_conn = Redis(host="127.0.0.1")
    q = Queue(connection=redis_conn)

    if q.remove(str(simulation.simulation_id)) > 0:
        # We removed one job. update status:
        update_sim_status(simulation.simulation_id, Simulation.Status.ABORTED)

    return HttpResponseRedirect(reverse("omnetppManager_job_status"))



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
        if step == "1":
            simulation_file = self.get_cleaned_data_for_step("0")["simulation_file"]
            omnetppini = simulation_file.read().decode("utf-8")
            simulation_file.seek(0)
            config = configparser.ConfigParser()
            config.read_string(omnetppini)
            sections = config.sections()
            # Remove HTML etc. -> XSS
            sections = [strip_tags(section) for section in sections]

            return self.initial_dict.get(step, {"sections" : sections})

        return self.initial_dict.get(step, {})

    # Form is finished, process the data, start the job
    def done(self, form_list, **kwargs):
        cleaned_data = self.get_all_cleaned_data()
        q = Queue(connection=Redis(host="127.0.0.1"))
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
                "omnetpp.ini" : str(omnetppini),
                "runconfig" : str(cleaned_data["simulation_name"]),
                "summarizing_precision" : float(cleaned_data["summarizing_precision"]),
                "storage_backend" : str(storage_backend_object.backend_name),
                "storage_backend_id" : str(storage_backend_object.backend_identifier),
                "storage_backend_token" : str(storage_backend_object.backend_token),
                }


        print("Simulation arguments:", args)


        # Start job
        job = q.enqueue(
                run_simulation,
                SimulationRuntimes.OPS_KEETCHI,
                args,
                job_timeout=settings.DEFAULT_SIMULATION_TIMEOUT,    # TODO: Get as param, make configurable?
                )
        print("Job with id", job.id, "started")

        # Store simulation including the job id for later
        simulation = Simulation(
                user = self.request.user,
                title = str(cleaned_data["simulation_title"]),
                omnetppini = str(omnetppini),
                runconfig = str(cleaned_data["simulation_name"]),
                simulation_id = job.id,
                summarizing_precision = float(cleaned_data["summarizing_precision"]),
                notification_mail_address = notification_mail_address,
                storage_backend = storage_backend_object,
                )

        simulation.save()

        # Redirect to detail view for simulation
        return redirect(simulation.get_absolute_url())


class JobDetailView(DetailView):
    model = Simulation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

## helper

## Update the status in the simulation db.
#
# Returns true, if something was updated
def update_sim_status(simulation_id, new_status):
    sim = None
    try:
        sim = Simulation.objects.get(simulation_id=simulation_id)
        if sim.status != new_status:
            sim.status = new_status
            sim.save()
            if sim.send_notify_mail():
                # Send status update mail
                send_mail(
                        "Simulation status update",
                        "The status of your simulation with the id " + str(simulation_id) + " has changed. New status: " + str(sim.get_status_display()),
                        settings.DEFAULT_SENDER_MAIL_ADDRESS,
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
def store_sim_results(simulation_id, meta, data):
    sim = None
    try:
        sim = Simulation.objects.get(simulation_id=simulation_id)
        if "exception" in meta:
            sim.simulation_error = meta["exception"]

        if "handled_by" in meta:
            sim.handled_by = meta["handled_by"]

        if isinstance(data, dict):
            print(data)
            if "shared_link" in data and data["shared_link"] and data["shared_link"] != "":
                sim.shared_link = data["shared_link"]
                print("Stored shared link")

        # TODO: store results / data

        sim.save()
        return True
    except Simulation.DoesNotExist:
        print("Simulation does not exist")
        sim = None
    return False
