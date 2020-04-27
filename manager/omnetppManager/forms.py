from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from django.conf import settings

import configparser

## Special field for uploading omnetpp.ini files.
#
# Check the following
# - filesize
# - mime-type
# - can be parsed as a valid ini file (i.e. has at least one section)
class OmnetppiniFileUploadField(forms.FileField):
    def validate(self, value):
        super().validate(value)
        if value.content_type not in settings.OMNETPPINI_ALLOWED_MIMETYPE:
            raise ValidationError(
                    _('Invalid file type. Only omnetpp.ini files are allowed.')
                    )
        if value.size > settings.OMNETPPINI_MAX_FILESIZE:
            raise ValidationError(
                    _('File too large. Maximum allowed size:  %(size)s kb'),
                    params={'size' : settings.OMNETPPINI_MAX_FILESIZE/1024}
                    )

        omnetppini = value.read().decode("utf-8")
        value.seek(0)
        config = configparser.ConfigParser()
        config.read_string(omnetppini)
        if len(config.sections()) < 1:
            raise ValidationError(
                    _('No run configurations found in omnetpp.ini'),
                    )

## Get the simulation name and upload a omnetpp.ini file
#
# Used for two step form
class getOmnetppiniForm(forms.Form):
    simulation_title = forms.CharField(max_length=50)
    simulation_file  = OmnetppiniFileUploadField()

## Select the simulation to run
#
# Used for two step form, choices are read from the omnetpp.ini file from
# step 1
class selectSimulationForm(forms.Form):
    summarizing_precision = forms.FloatField(label="precision", initial=100.0, help_text="Average values every N seconds")
    notification_mail_address = forms.EmailField(label="notify simulation state changes (optional)", required=False, help_text="A mail address or leave it empty to disable notification")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_args = kwargs.get("initial", None)
        if init_args and "sections" in init_args:
            self.fields["simulation_name"] = \
                    forms.CharField(
                            label="Select simulation",
                            widget=forms.Select(choices=[(sec, sec) for sec in init_args["sections"]]),
                            help_text="simulation name from previously uploaded omnetpp.ini"
                            )




