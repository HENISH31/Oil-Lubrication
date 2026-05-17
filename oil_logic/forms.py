from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import Maintenance

class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Enter your email address")
    username = forms.CharField(max_length=150, required=False, help_text="Optional: Choose a unique username. If left blank, we will use your email prefix.")
    full_name = forms.CharField(max_length=100, required=True, help_text="Enter your full name")
    tagline = forms.CharField(max_length=255, required=False, help_text="Optional: A short tagline for your profile.")
    referral_code = forms.CharField(max_length=20, required=False, help_text="Optional: Did a friend refer you? Enter their code for ₹50 bonus!")
    
    class Meta(UserCreationForm.Meta):
        fields = ('email', 'username', 'full_name', 'tagline', 'referral_code')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We want to keep username in fields but make it not required
        self.fields['username'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            return email.lower()
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name')
        email = self.cleaned_data.get('email')
        manual_username = self.cleaned_data.get('username')
        tagline = self.cleaned_data.get('tagline')
        
        user.email = email
        
        if manual_username:
            user.username = manual_username
        elif email:
            base_username = email.split('@')[0]
            # Ensure unique username
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username
            
        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
        
        if commit:
            user.save()
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.tagline = tagline
            profile.save()
        return user

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))
    
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            email = email.lower()
            # Check if user exists with this email (case-insensitive for backward compatibility)
            try:
                user = User.objects.get(email__iexact=email)
                self.user_cache = authenticate(self.request, username=user.username, password=password)
                if self.user_cache is None:
                    raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')
                else:
                    self.confirm_login_allowed(self.user_cache)
            except User.DoesNotExist:
                raise forms.ValidationError("No account found with this email.", code='invalid_login')

        return self.cleaned_data

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

class LocatorForm(forms.Form):
    q = forms.CharField(
        label="City or Zip Code",
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter City or Zip Code',
            'class': 'w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white placeholder-gray-600 focus:border-red-500/50 focus:outline-none transition-all'
        })
    )
