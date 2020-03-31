from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import FileSystemStorage
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


def redirect_to_here(request):
    return HttpResponseRedirect(reverse("omnetppManager_index"))

@login_required
def index(request):
    return render(request, 'omnetppManager/index.html', {})

@login_required
def status(request):
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

    return render(request, 'omnetppManager/statusPage.html', {
            "status" : status,
        })


def manage_queues(request):

    redis_conn = Redis(host="127.0.0.1")
    q = Queue(connection=redis_conn)

    finished_jobs = len(q.finished_job_registry)
    failed_jobs = len(q.failed_job_registry)

    for j in q.finished_job_registry.get_job_ids():
        job = q.fetch_job(j)
        print("ID", j)
        print(job.result)
        print(job.meta)
        q.finished_job_registry.remove(job)


    for j in q.failed_job_registry.get_job_ids():
        job = q.fetch_job(j)
        print(job.id)

        q.failed_job_registry.remove(job)

    """
    print("Jobs in queue", len(q))
    print("Finished jobs:", len(q.finished_job_registry))
    print("Failed jobs:", len(q.failed_job_registry))
    print("Started jobs:", len(q.started_job_registry))
    print("Deferred jobs:", len(q.deferred_job_registry))
    print("Scheduled jobs:", len(q.scheduled_job_registry))
    """


    return render(request, 'omnetppManager/manage_queues.html',
            {
                "failed_jobs" : failed_jobs,
                "finished_jobs" : finished_jobs,
            }
            )



class NewSimWizard(SessionWizardView):
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_omnetppini_files'))
    template_name = 'omnetppManager/start_simulation.html'

    def get_form_initial(self, step):

        if step == "1":
            simulation_file = self.get_cleaned_data_for_step("0")["simulation_file"]
            omnetppini = simulation_file.read().decode("utf-8")
            simulation_file.seek(0)
            config = configparser.ConfigParser()
            config.read_string(omnetppini)
            sections = config.sections()
            sections = [strip_tags(section) for section in sections]

            return self.initial_dict.get(step, {"sections" : sections})

        return self.initial_dict.get(step, {})

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


        job = q.enqueue(
                run_simulation,
                SimulationRuntimes.OPS_KEETCHI,
                args,
                )
        job.id

        simulation = Simulation(
                user = self.request.user,
                title = str(cleaned_data["simulation_title"]),
                omnetppini = str(omnetppini),
                runconfig = str(cleaned_data["simulation_name"]),
                simulation_id = job.id,
                )

        simulation.save()


        return redirect("/")
