from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.utils.html import strip_tags

from formtools.wizard.views import SessionWizardView

from .models import Simulation

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
# TODO: Maybe w/o HTML, json return? Increase security?
def manage_queues(request, output_format="json"):
    redis_conn = Redis(host="127.0.0.1")
    q = Queue(connection=redis_conn)

    finished_jobs = len(q.finished_job_registry)
    failed_jobs = len(q.failed_job_registry)

    updated_jobs = 0

    update_sim_status("1d244db6-085c-440a-a4d8-c2e83497764b", Simulation.Status.STARTED)

    for j in q.finished_job_registry.get_job_ids():
        update_sim_status(j, Simulation.Status.FINISHED)

        job = q.fetch_job(j)
        print("ID", j)
        print(job.result)
        print(job.meta)
        q.finished_job_registry.remove(job)


    for j in q.failed_job_registry.get_job_ids():
        update_sim_status(j, Simulation.Status.FAILED)

        job = q.fetch_job(j)
        print(job.id)
        print(job.meta)

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

        args = {
                "user" : str(self.request.user),
                "title" : str(cleaned_data["simulation_title"]),
                "omnetpp.ini" : str(omnetppini),
                "runconfig" : str(cleaned_data["simulation_name"]),
                }


        # Start job
        job = q.enqueue(
                run_simulation,
                SimulationRuntimes.OPS_KEETCHI,
                args,
                )
        print("Job with id", job.id, "started")

        # Store simulation including the job id for later
        simulation = Simulation(
                user = self.request.user,
                title = str(cleaned_data["simulation_title"]),
                omnetppini = str(omnetppini),
                runconfig = str(cleaned_data["simulation_name"]),
                simulation_id = job.id,
                )

        simulation.save()


        # Go to index. TODO: Give feedback to user
        return redirect("/")


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
            return True
    except Simulation.DoesNotExist:
        print("Sim does not exists in db")
        sim = None
        pass

    return False

