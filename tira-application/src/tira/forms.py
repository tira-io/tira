from django import forms


class LoginForm(forms.Form):
    user_id = forms.CharField(label="User ID", max_length=100,
                              widget=forms.TextInput(attrs={"class": "uk-input", "placeholder": "Enter Tira User ID"}))
    password = forms.CharField(label="Password", max_length=100,
                              widget=forms.PasswordInput(attrs={"class": "uk-input", "placeholder": "Enter Password"}))
