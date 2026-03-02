from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Maintenance

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

class OilRecommendationForm(forms.Form):
    driving_condition = forms.ChoiceField(
        choices=Maintenance.DRIVING_CONDITIONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mileage_range = forms.ChoiceField(
        choices=Maintenance.MILEAGE_RANGES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    preferred_frequency = forms.ChoiceField(
        choices=Maintenance.OIL_CHANGE_FREQUENCIES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
