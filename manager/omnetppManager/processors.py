# Content processors

from django.conf import settings

## General information required for each page:
def get_general(request):
    return {
            "manager_general" : {
                "base_title" : settings.DEFAULT_MAIN_TITLE,
                }
            }
