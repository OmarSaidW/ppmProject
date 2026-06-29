from django import forms
from datetime import datetime
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

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('date_time_start')
        end = cleaned_data.get('date_time_end')
        now = datetime.now()
        if start and 'date_time_start' in self.changed_data and start < now:
            self.add_error('date_time_start', 'La data di inizio non può essere nel passato.')
        if end and 'date_time_end' in self.changed_data and end < now:
            self.add_error('date_time_end', 'La data di fine non può essere nel passato.')
        if start and end and end < start:
            self.add_error('date_time_end', 'La data di fine deve essere successiva a quella di inizio.')
        return cleaned_data


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

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('date_time_start')
        end = cleaned_data.get('date_time_end')
        deadline = cleaned_data.get('invitation_deadline')
        now = datetime.now()
        if start and 'date_time_start' in self.changed_data and start < now:
            self.add_error('date_time_start', 'La data di inizio non può essere nel passato.')
        if end and 'date_time_end' in self.changed_data and end < now:
            self.add_error('date_time_end', 'La data di fine non può essere nel passato.')
        if start and end and end < start:
            self.add_error('date_time_end', 'La data di fine deve essere successiva a quella di inizio.')
        if deadline and 'invitation_deadline' in self.changed_data and deadline < now:
            self.add_error('invitation_deadline', 'La scadenza inviti non può essere nel passato.')
        if deadline and start and deadline > start:
            self.add_error('invitation_deadline', 'La scadenza inviti deve essere precedente alla data di inizio evento.')
        return cleaned_data