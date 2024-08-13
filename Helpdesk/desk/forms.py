from django.forms import ModelForm, Textarea, TextInput, Select, CharField, PasswordInput
from .models import Ticket, UserProfile
from django import forms
from django.contrib.auth.backends import BaseBackend
from .models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

class VerboseNameBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user_profile = UserProfile.objects.get(verbose_name=username)
            user = user_profile.user
            if user.check_password(password):
                return user
        except UserProfile.DoesNotExist:
            pass
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'content', 'criticalness')
        widgets = {
            'title': TextInput(attrs={'class': 'form-control'}),
            'content': Textarea(attrs={'class': 'form-control'}),
            'criticalness': Select(attrs={'class': 'form-select'}, choices = Ticket.Kinds.choices),
        }
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields.pop('technician')
        
class LoginForm(forms.Form):
    username = forms.ModelChoiceField(queryset=UserProfile.objects.all(), empty_label='Выберите пользователя...', label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
