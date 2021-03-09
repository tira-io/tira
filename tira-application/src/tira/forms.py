from django import forms


class LoginForm(forms.Form):
    user_id = forms.CharField(label="User ID", max_length=100,
                              widget=forms.TextInput(attrs={"class": "uk-input", "placeholder": "Enter Tira User ID"}))
    password = forms.CharField(label="Password", max_length=100,
                               widget=forms.PasswordInput(attrs={"class": "uk-input", "placeholder": "Enter Password"}))


class CreateVmForm(forms.Form):
    """ hostname,vm_id,ova_id"""
    bulk_create = forms.CharField(label="Enter VMs to be created (newline separated)!",
                                  widget=forms.Textarea(attrs={"class": "uk-textarea", "rows": "5",
                                                               "placeholder": "hostname,vm_id_1,ova_id\nhostname,vm_id_2,..."}))
