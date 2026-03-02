from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True, help_text="Enter your full name")
    
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('full_name',)

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name')
        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
        if commit:
            user.save()
        return user
