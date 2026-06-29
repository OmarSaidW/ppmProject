from django import forms
from .models import PublicEvent, EventoPrivato


class PublicEventForm(forms.ModelForm):
    class Meta:
        model = PublicEvent
        fields = [
            'title', 'description', 'date_time_start', 'date_time_end', 'location',
            'supervisor', 'organizers',
            'ticket_price', 'public_visibility', 'registration_required', 'max_participants',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Titolo dell'evento"}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_time_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_time_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Luogo'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'}),
            'organizers': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'ticket_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class EventoPrivatoForm(forms.ModelForm):
    class Meta:
        model = EventoPrivato
        fields = [
            'title', 'description', 'date_time_start', 'date_time_end', 'location',
            'supervisor', 'organizers',
            'invite_code', 'invitation_deadline', 'approval_required', 'secret_location',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Titolo dell'evento"}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_time_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'date_time_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Luogo'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'}),
            'organizers': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'invite_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Codice invito univoco'}),
            'invitation_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }