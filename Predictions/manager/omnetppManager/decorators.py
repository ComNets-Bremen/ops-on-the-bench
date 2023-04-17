from django.http import HttpResponse
from django.shortcuts import redirect

#from background_task import background
from rq import Queue
from rq.job import Job
from redis import Redis
from rq.command import send_stop_job_command

#from .models import ConfigKeyValueStorage

## redirect to home page when users is already authenticated
def already_authenticated(in_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('omnetppManager_index')
        else:
            return in_func(request, *args, **kwargs)

    return wrapper_func

## redirect to home page when users is not authenticated
def auth_required(in_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('omnetppManager_index')
        else:
            return in_func(request, *args, **kwargs)

    return wrapper_func
    
    
    
#@background(schedule=2)
#def notify_user(name):
#    print(f"HELLO {name}")
#    
#    host = ConfigKeyValueStorage.config.get_value("REDIS_DB_HOST", "localhost")
#    port = ConfigKeyValueStorage.config.get_value("REDIS_DB_PORT", 6379)
#    password = ConfigKeyValueStorage.config.get_value("REDIS_DB_PASSWORD", None)
#    
#    r = Redis(host=host, port=port, password=password)
#    q = Queue(connection=r)
#    print("Redis Connection Established")
#    print("JOBS IN THE QUEUE CURRENLTY : ", q.job_ids)
#    r.close()
#    print("Redis Connection Closed")
