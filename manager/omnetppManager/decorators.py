from django.http import HttpResponse
from django.shortcuts import redirect


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