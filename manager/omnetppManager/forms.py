from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from django.conf import settings

import configparser

# Check for content type and filesize
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

class getOmnetppiniForm(forms.Form):
    simulation_title = forms.CharField(max_length=50)
    simulation_file  = OmnetppiniFileUploadField()

class selectSimulationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_args = kwargs.get("initial", None)
        if init_args and "sections" in init_args:
            self.fields["simulation_name"] = \
                    forms.CharField(
                            label="Select simulation",
                            widget=forms.Select(choices=[(sec, sec) for sec in init_args["sections"]])
                            )



