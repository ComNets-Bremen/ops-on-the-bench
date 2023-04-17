from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Q, fields
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from django.forms import BaseFormSet

import configparser

from django.db.utils import OperationalError

from .models import StorageBackend, OmnetppConfigType, OmnetppConfig, OmnetppConfigParameter,\
     OmnetppBenchmarkConfig, OmnetppBenchmarkParameters, OmnetppBenchmarkEditableParameters, OmnetppBenchmarkForwarderConfig, OmnetppBenchmarkForwarderParameters



## User Registration form
class CreateUsers(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.Meta.required:
            self.fields[field].required = True
            
    password1 = forms.CharField(max_length=16, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}))
    password2 = forms.CharField(max_length=16, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }
        required = ('username', 'email', 'password1', 'password2',)


class ModelPredictionForm(forms.Form):
    peak_disk_usage = forms.CharField(disabled=True, initial="This field is read-only",label = "Peak Disk Usage")
    peak_RAM_usage_simulation = forms.CharField(disabled=True, initial="This field is read-only",label = "Peak RAM Usage (Simulation)")
    peak_RAM_usage_results = forms.CharField(disabled=True, initial="This field is read-only",label = "Peak RAM usage (Results Parsing)")
    total_time_taken = forms.CharField(disabled=True, initial="This field is read-only",label = "Total Time Taken")
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['peak_disk_usage'].widget.attrs['readonly'] = True
        self.fields['peak_RAM_usage_simulation'].widget.attrs['readonly'] = True
        self.fields['peak_RAM_usage_results'].widget.attrs['readonly'] = True
        self.fields['total_time_taken'].widget.attrs['readonly'] = True
    
    
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
        try:
            config.read_string(omnetppini)
        except configparser.DuplicateSectionError:
            raise ValidationError(
                    _('This omnetpp.ini contains duplicate sections.'),
                    )
        if len(config.sections()) < 1:
            raise ValidationError(
                    _('No run configurations found in omnetpp.ini'),
                    )

## Get the simulation name and upload a omnetpp.ini file
#
# Used for two step form
class getOmnetppiniForm(forms.Form):
    simulation_title = forms.CharField(max_length=50)
    simulation_file  = OmnetppiniFileUploadField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    is_debug_sim     = forms.BooleanField(label="Debug simulation", help_text="This simulation is for debugging. Do not count for statistics.", required=False)


## Select the simulation to run
#
# Used for two step form, choices are read from the omnetpp.ini file from
# step 1
class selectSimulationForm(forms.Form):
    summarizing_precision = forms.FloatField(label="precision", initial=100.0, help_text="Average values every N seconds")
    summarizing_precision.widget.attrs.update({"class" : "form-control"})

    notification_mail_address = forms.EmailField(label="notify simulation state changes (optional)", required=False, help_text="A mail address or leave it empty to disable notification")
    notification_mail_address.widget.attrs.update({"class" : "form-control"})

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
            self.fields["simulation_name"].widget.attrs.update({"class" : "form-control"})


        storage_names = []

        for item in StorageBackend.objects.filter(backend_active=True).values("pk", "backend_name"):
            storage_names.append((item["pk"], item["backend_name"]))

        self.fields["storage_backend"] = forms.CharField(
                label="Select storage backend",
                widget=forms.Select(
                    choices=storage_names,
                    attrs={
                    "class" : "form-control",
                    },
                ),
                help_text="Storage backend for the simulation output"
                )


# Omnetpp Benchmark forms 
#      
# simulatiion title and simulation name form
class getOmnetppBenchmarkSection(forms.Form):
    simulation_title = forms.CharField(max_length=50)
    try:
        sections = OmnetppBenchmarkConfig.objects.filter(~Q(name='General'))
        simulation_name = \
                forms.CharField(
                    label="Select simulation",
                    widget=forms.Select(choices=[(sec, sec) for sec in sections]),
                    help_text="simulation name from omnetpp-ops-benchmark.ini"
                    )
        simulation_name.widget.attrs.update({"class" : "form-control"})
    except OperationalError:
        pass # when db doesn't exist yet


# forwarding layer selection form 
class selectForwarderForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_args = kwargs.get("initial", None)
        if init_args and "section_name" in init_args:
            f_layers = OmnetppBenchmarkForwarderConfig.objects.all()
            self.fields["forwarding_layer"] = \
                    forms.CharField(
                            label="Forwarding Layer",
                            widget=forms.Select(choices=[(sec, sec) for sec in f_layers]),
                            help_text=f'Select a Forwarding layer for your selected simulation: { init_args["section_name"]}'
                            )
            self.fields["forwarding_layer"].widget.attrs.update({"class" : "form-control"})

class UserEditorForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_args = kwargs.get("initial", None)
        if (init_args and "forwarder" in init_args):
            global forward_var
            forward_var= init_args["forwarder"]
            
            # RNG Section
            g_section= OmnetppBenchmarkConfig.objects.filter(Q(name='General'))
            # print(g_section)
            rngs=OmnetppBenchmarkEditableParameters.objects.filter(config=g_section[0],user_editable=True)
            # print(rngs, len(rngs))
            for rng in range(0,len(rngs)):
                self.fields[rngs[rng]] = \
                        forms.IntegerField(
                                label=rngs[rng],
                                initial=rngs[rng].param_default_value,
                                max_value=10000,
                                min_value=0,
                                widget=forms.TextInput(attrs={
                                "class" : "form-control rng",
                                "placeholder":"Enter value here",
                                }),
                                help_text=f'{ rngs[rng].param_description:}' if rngs[rng].param_description else '',
                                )
                self.fields[rngs[rng]].widget.attrs.update({"class" : "form-control rng"})

            # Forwarding layer section
            f_layer = OmnetppBenchmarkForwarderConfig.objects.filter(name=init_args["forwarder"])
            params=OmnetppBenchmarkForwarderParameters.objects.filter(config =f_layer[0]).exclude(param_type=1).all()
            
            for p in params:
                self.fields[p] = \
                        forms.CharField(
                                label=p.param_display_name,
                                initial=p.param_default_value,
                                widget=forms.TextInput(attrs={
                                "class" : "form-control",
                                "placeholder":p.param_default_value,
                                }),
                                help_text=f'unit: { p.param_unit:}' if p.param_unit else '',
                                )
                self.fields[p].widget.attrs.update({"class" : "form-control"})

    def clean(self):
        cleaned_data = super().clean()
        # cc_myself = cleaned_data.get("cc_myself")
        # print(cleaned_data)
        # print(self.fields)
        # print(self.data)

        # g_section= OmnetppBenchmarkConfig.objects.filter(Q(name='General'))
        # rngs=OmnetppBenchmarkEditableParameters.objects.filter(config=g_section[0],user_editable=True).values_list('param_name',flat=True)
        f_layer = OmnetppBenchmarkForwarderConfig.objects.filter(name=forward_var)
        params=OmnetppBenchmarkForwarderParameters.objects.filter(config =f_layer[0]).exclude(param_type=1).all()
        params_range= OmnetppBenchmarkForwarderParameters.objects.filter(config =f_layer[0],param_type=2).values_list('param_name',flat=True)
        # print(rngs)
        for field in self.fields:
            strfield=str(field)
            if not self[field].html_name in self.data:
                return self.data
            # check if inout is numeric
            if strfield in params_range:#
                if cleaned_data.get(field).replace('.','',1).isdigit() == False:
                    raise forms.ValidationError({field : "This field must be a valid number"})
            if strfield != '':
                for display_name in params:
                    if field == display_name:
                        # clean data for ser editable range
                        if display_name.param_type == 2:
                            if float(cleaned_data.get(field)) < float(display_name.param_user_option.split(',')[0]) or float(cleaned_data.get(field)) > float(display_name.param_user_option.split(',')[1]):
                                raise forms.ValidationError({field :f"{display_name.param_display_name} should be between {display_name.param_user_option.split(',')[0]} and {display_name.param_user_option.split(',')[1]}" })

                        # clean data for user editable options
                        if display_name.param_type == 3:
                            if cleaned_data.get(field) not in  display_name.param_user_option.replace(" ", "").split(','):
                                raise forms.ValidationError({field :f"{display_name.param_display_name} should be one of the following: {', '.join([x for x in display_name.param_user_option.split(',')])} " })

       
        return cleaned_data
    
    
    def get_fields(self):
        return self.cleaned_data

#Benchmark General detail settings form
class BenchmarkGeneralSettingForm(forms.Form):

    notification_mail_address = forms.EmailField(label="notify simulation state changes (optional)", required=False, help_text="A mail address or leave it empty to disable notification")
    notification_mail_address.widget.attrs.update({"class":"form-control"})

    summarizing_precision = forms.FloatField(label="precision", initial=100.0, help_text="Average values every N seconds")
    summarizing_precision.widget.attrs.update({"class" : "form-control"})


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        storage_names = []

        for item in StorageBackend.objects.filter(backend_active=True).values("pk", "backend_name"):
            storage_names.append((item["pk"], item["backend_name"]))

        self.fields["storage_backend"] = forms.CharField(
                label="Select storage backend",
                widget=forms.Select(
                    choices=storage_names,
                    attrs = {
                        "class" : "form-control",
                        },
                    ),
                help_text="Storage backend for the simulation output"
                )




    def get_fields(self):
        return self.cleaned_data
#
# end of benchmark forms


# Guest user omnetpp config forms


# General detailed settings form
class GeneralSettingForm(forms.Form):
    simulation_title = forms.CharField(max_length=50)
    simulation_title.widget.attrs.update({"class":"form-control"})

    notification_mail_address = forms.EmailField(label="notify simulation state changes (optional)", required=False, help_text="A mail address or leave it empty to disable notification")
    notification_mail_address.widget.attrs.update({"class":"form-control"})

    summarizing_precision = forms.FloatField(label="precision", initial=100.0, help_text="Average values every N seconds")
    summarizing_precision.widget.attrs.update({"class" : "form-control"})

    advanced_settings = forms.BooleanField(label="Advanced settings", help_text="Show advanced settings", required=False)
    advanced_settings.widget.attrs.update({"class" : "form-control"})



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        types = OmnetppConfigType.objects.filter(has_multiple_instances=False)
        for t in types:
            options = OmnetppConfig.objects.filter(model_type=t)
            name = "generalSetting_"+"".join(t.name.split(" "))
            self.fields[name] = forms.CharField(
                    label = t.label,
                    widget=forms.Select(
                        choices = [[o.id, o.name] for o in options],
                        attrs = {
                            "class" : "form-control",
                            }
                        )
                    )

        storage_names = []

        for item in StorageBackend.objects.filter(backend_active=True).values("pk", "backend_name"):
            storage_names.append((item["pk"], item["backend_name"]))

        self.fields["storage_backend"] = forms.CharField(
                label="Select storage backend",
                widget=forms.Select(
                    choices=storage_names,
                    attrs = {
                        "class" : "form-control",
                        },
                    ),
                help_text="Storage backend for the simulation output"
                )




    def get_fields(self):
        return self.cleaned_data

# set the models for the nodes
class NodeSettingForm(forms.Form):
    name = forms.CharField(
            label="Node Name",
            widget=forms.TextInput(attrs={
                "class" : "form-control",
                "placeholder":"Enter name here",
                })
            )
    node_number = forms.DecimalField(
            label="Number of nodes",
            widget=forms.NumberInput(attrs={
                "class" : "form-control",
                "placeholder" : 0,
                })
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        types = OmnetppConfigType.objects.filter(has_multiple_instances=True)

        for t in types:

            options = OmnetppConfig.objects.filter(model_type=t)

            name = "setting_"+"".join(t.name.split(" "))
            self.fields[name] = forms.CharField(
                    label = t.label,
                    widget=forms.Select(
                        choices = [[o.id, o.name] for o in options],
                        attrs={
                            "class" : "form-control",
                            "placeholder" : t.label,
                            }),
                        )


    def get_fields(self):
        return self.cleaned_data



class BaseNodeSettingFormSet(BaseFormSet):
    def clean(self):
        node_names = []

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            node_name = form.cleaned_data.get("name")
            if node_name in node_names:
                raise forms.ValidationError("Nodes in a set must have distinct names.")
            node_names.append(node_name)



# Detailed config
class ModelDetailSettingForm(forms.Form):
    parameters = {}

    def __init__(self, *args, **kwargs):
        base_data = None
        data = None
        advanced = None

        if "base_sim_settings" in kwargs:
            base_data = kwargs.pop("base_sim_settings")
            advanced = base_data["advanced_settings"]

        if "nodes_sim_settings" in kwargs:
            data = kwargs.pop("nodes_sim_settings")

        super().__init__(*args, **kwargs)


        field_count = 0

        total_number_nodes = 0

        ## First handle general simulation settings

        if base_data:
            for s in base_data:
                if not s.startswith("generalSetting_"):
                    continue
                base_objects = OmnetppConfig.objects.filter(id__in=base_data[s]).all()
                for field in base_objects:
                    parameters = OmnetppConfigParameter.objects.filter(config__id=field.id).all()
                    multiple = None
                    for p in parameters:
                        if multiple==None:
                            multiple = p.config.model_type.has_multiple_instances
                        f = forms.CharField(
                                label= p.param_name,
                                disabled=not p.user_editable,
                                help_text = p.param_description,
                                initial=p.param_default_value + str(p.param_unit),
                                )
                        f.widget.attrs.update({"class" : "form-control"})
                        if not advanced and not p.user_editable:
                            f.widget = forms.HiddenInput()

                        field_name = "field_"+str(field_count)
                        self.fields[field_name] = f
                        field_count += 1
                        self.parameters[field_name] = {
                                "param_name" : p.param_name,
                                "user_editable" : p.user_editable,
                                "param_default_value" : p.param_default_value,
                                "param_unit" : p.param_unit,
                                }

        ## Base settings done, now start with user defined settings
        if data:
            for notegroupsetting in data:
                number_nodes = notegroupsetting["node_number"]
                for subsetting in notegroupsetting:
                    if not subsetting.startswith("setting_"):
                        continue
                    nodes_setting_objects = OmnetppConfigParameter.objects.filter(config__id=notegroupsetting[subsetting]).all()
                    multiple = None

                    for setting in nodes_setting_objects:
                        if multiple == None:
                            multiple = setting.config.model_type.has_multiple_instances

                        param_name = setting.param_name
                        if multiple and param_name.startswith("**."):
                            param_name = "**.host[" + str(total_number_nodes) + ".." + str(total_number_nodes+number_nodes-1) + "]." + param_name[3:]
                        f = forms.CharField(
                                label=param_name,
                                disabled = not setting.user_editable,
                                help_text = setting.param_description,
                                initial=setting.param_default_value + str(setting.param_unit),
                                )
                        f.widget.attrs.update({"class" : "form-control"})
                        if not advanced and not setting.user_editable:
                            f.widget = forms.HiddenInput()

                        field_name = "field_"+str(field_count)
                        self.fields[field_name] = f
                        field_count += 1
                        self.parameters[field_name] = {
                                "param_name" : param_name,
                                "user_editable" : setting.user_editable,
                                "param_default_value" : setting.param_default_value,
                                "param_unit" : setting.param_unit,
                                }



                total_number_nodes += number_nodes

        ## Static (context-generated) parameters

        f = forms.CharField(
                label="**.numNodes",
                disabled=True,
                help_text = "Total number of nodes",
                initial = total_number_nodes,
                )
        f.widget.attrs.update({"class" : "form-control"})
        if not advanced:
            f.widget = forms.HiddenInput()
        field_name = "field_" + str(field_count),
        self.fields[field_name] = f
        field_count += 1
        self.parameters[field_name] = {
                "param_name" : "**.numNodes",
                "user_editable" : False,
                "param_default_value" : total_number_nodes,
                "param_unit" : "",
                }

    def get_fields(self):
        r = {}

        for field in self.fields:
            if field in self.parameters:
                if self.parameters[field]["user_editable"]:
                    r[self.parameters[field]["param_name"]] = self.cleaned_data[field]
                else:
                    r[self.parameters[field]["param_name"]] = str(self.parameters[field]["param_default_value"]) + str(self.parameters[field]["param_unit"])
            else:
                r[field] = self.cleaned_data[field]
        return r


class RequestAccessForm(forms.Form):
    name = forms.CharField(label='Your name', max_length=100, help_text="Your full name.")
    mail = forms.EmailField(label='Your mail address', help_text="The mail address we will use to contact you.")
    affiliation = forms.CharField(label='Your affiliation', max_length=100, help_text="For whom are you working?")
    interest = forms.CharField(widget=forms.Textarea, label="Interest", max_length=4000, min_length=10, help_text="A brief description why this project is interesting for you and for what you would like to use it.")



class RerunSimForm(forms.Form):
    simulation_title = forms.CharField(max_length=50)
    simulation_title.widget.attrs.update({"class":"form-control"})

