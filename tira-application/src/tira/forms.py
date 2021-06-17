from django import forms


class LoginForm(forms.Form):
    user_id = forms.CharField(label="User ID", max_length=100,
                              widget=forms.TextInput(attrs={"class": "uk-input", "placeholder": "Enter Tira User ID"}))
    password = forms.CharField(label="Password", max_length=100,
                               widget=forms.PasswordInput(attrs={"class": "uk-input", "placeholder": "Enter Password"}))


class CreateVmForm(forms.Form):
    """ hostname,vm_id,ova_id"""
    bulk_create = forms.CharField(label="Enter VMs to be created (newline separated)",
                                  widget=forms.Textarea(attrs={"class": "uk-textarea", "rows": "5",
                                                               "placeholder": "hostname,vm_id_1,ova_id\nhostname,vm_id_2,..."}))


class ArchiveVmForm(forms.Form):
    bulk_archive = forms.CharField(label="Enter VM_IDs to be archived (newline separated)",
                                   widget=forms.Textarea(attrs={"class": "uk-textarea", "rows": "5",
                                                                "placeholder": "vm_id_1\nvm_id_2\n..."}))


class ModifyVmForm(forms.Form):
    vm_id = forms.CharField(label="VM ID", max_length=200,
                            widget=forms.TextInput(attrs={"class": "uk-input", "placeholder": "Enter Tira VM ID"}))
    memory = forms.IntegerField(label="Memory (GB)", min_value=1, max_value=128,
                                widget=forms.NumberInput(attrs={"class": "uk-input"}))
    cpu = forms.IntegerField(label="CPU", min_value=1, max_value=32,
                             widget=forms.NumberInput(attrs={"class": "uk-input"}))
    storage = forms.IntegerField(label="Storage (GB)", min_value=1, max_value=4000,
                                 widget=forms.NumberInput(attrs={"class": "uk-input"}))
    storage_type = forms.ChoiceField(label="Storage Type", choices=[("HDD", "HDD"), ("SFTP", "SFTP")],
                                     widget=forms.Select(attrs={"class": "uk-select"}))


class CreateTaskForm(forms.Form):
    """ task_id, task_name, task_description, organizer, website """
    task_id = forms.CharField(label="Task ID", max_length=100,
                              widget=forms.TextInput(attrs={"class": "uk-input",
                                                            "placeholder": "task-id-lowercase-with-dashes"}))
    task_name = forms.CharField(label="Task Name", max_length=200,
                                widget=forms.TextInput(attrs={"class": "uk-input",
                                                              "placeholder": "Titlecase Name of the Task."}))
    master_vm_id = forms.CharField(label="Master VM_ID", max_length=200,
                                   widget=forms.TextInput(attrs={"class": "uk-input",
                                                                 "placeholder": "id-lowercase-with-dashes"}))
    organizer = forms.CharField(label="Host_ID", max_length=100,
                                widget=forms.TextInput(attrs={"class": "uk-input"}))
    website = forms.URLField(label="Task Website", max_length=200, initial='http://',
                             widget=forms.URLInput(attrs={"class": "uk-input"}))
    task_description = forms.CharField(label="Task Description",
                                       widget=forms.Textarea(attrs={"class": "uk-textarea", "rows": "3",
                                                                    "placeholder": "Describe your task"}))


class AddDatasetForm(forms.Form):
    """ id_prefix, dataset_name, evaluator: master_vm_id, command, workingDirectory, measures, measureKeys  """
    task_id = forms.CharField(label="For Task ID", max_length=100, required=True,
                              widget=forms.TextInput(attrs={"class": "uk-input",
                                                            "placeholder": "task-id-lowercase-with-dashes"}))

    dataset_id_prefix = forms.SlugField(label="Dataset ID prefix", max_length=200, required=True,
                                        widget=forms.TextInput(attrs={"class": "uk-input"}))

    dataset_name = forms.CharField(label="Dataset Name", max_length=200, required=True,
                                   widget=forms.TextInput(attrs={"class": "uk-input",
                                                                 "placeholder": "Titlecase Name of the Dataset."}))
    create_training = forms.BooleanField(label="training", required=False, initial=True,
                                         widget=forms.CheckboxInput(attrs={"class": "uk-checkbox"}))
    create_test = forms.BooleanField(label="test", required=False, initial=True,
                                     widget=forms.CheckboxInput(attrs={"class": "uk-checkbox"}))
    create_dev = forms.BooleanField(label="dev", required=False,
                                    widget=forms.CheckboxInput(attrs={"class": "uk-checkbox"}))

    master_vm_id = forms.CharField(label="Master VM_ID", max_length=200, required=True,
                                   widget=forms.TextInput(attrs={"class": "uk-input",
                                                                 "placeholder": "id-lowercase-with-dashes"}))
    command = forms.CharField(label="Evaluator Command", max_length=200, required=False,
                              widget=forms.TextInput(attrs={"class": "uk-input",
                                                            "placeholder": "Command to be run from working directory."}))
    working_directory = forms.CharField(label="Evaluator Working Directory", max_length=200, required=False,
                                        widget=forms.TextInput(attrs={"class": "uk-input",
                                                                      "placeholder": "/path/to/directory. Defaults to home."}))
    measures = forms.CharField(label="Measures (separate by newline)", required=False,
                               widget=forms.Textarea(attrs={"class": "uk-textarea", "rows": "5",
                                                            "placeholder": "Measure Name,measure_key\n"
                                                                           "Name will be displayed to the users.\n"
                                                                           "measure_key must be as output by the evaluation software."}))


class ReviewForm(forms.Form):
    """ Form to create Reviews. Delivered on the tira.review route and handeled by the review view."""
    no_errors = forms.BooleanField(label="No Errors", required=False,
                                   widget=forms.CheckboxInput(attrs={"id": "no-error-checkbox", "class": "uk-checkbox"}))
    output_error = forms.BooleanField(label="Output Error", required=False,
                                        widget=forms.CheckboxInput(attrs={"id": "output-error-checkbox", "class": "uk-checkbox"}))
    software_error = forms.BooleanField(label="Software Error", required=False,
                                      widget=forms.CheckboxInput(attrs={"id": "software-error-checkbox", "class": "uk-checkbox"}))
    comment = forms.CharField(label="Comment", required=False,
                              widget=forms.Textarea(attrs={"class": "uk-textarea", "rows": "6"}))
