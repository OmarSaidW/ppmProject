from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django import forms

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('telefono',)
        def save(self, commit=True):
        # Intercettiamo il salvataggio per impostare il ruolo di default
            user = super().save(commit=False)
            user.ruolo = 'ATTENDEE'  # Forza il ruolo a Partecipante
            if commit:
                user.save()
            return user

#Due form : entrambi gestiscono la modifica del profilo ma lo fanno in base al tipo di utente
class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'telefono'] # L'utente non può cambiare il suo username o ruolo qui

class OrganizerChangeRoleForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['ruolo']