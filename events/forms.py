from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import  Event


#Form inserimento evento
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'supervisor', 'organizers']
        #I widgets permettono di definire come vengono visualizzati i campi del form
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titolo dell\'evento'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrizione'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Luogo'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'}),
            'organizers': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }