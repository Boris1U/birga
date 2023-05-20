from django.contrib.auth import forms

from .models import Profile


class ProfileCreationForm(forms.UserCreationForm):
    class Meta(forms.UserCreationForm):
        model = Profile
        fields = ('username', 'email')