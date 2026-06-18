from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import  Event


#Form inserimento evento
class EventForm(forms.ModelForm):
    class Meta: #La classe meta specifica quali campi prendere del model form Event
        model = Event
        fields = ['title', 'description', 'date', 'location', 'supervisor', 'organizers']
        
        #Personalizzazione grafica dei campi (Widget)
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titolo dell\'evento'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrizione'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Luogo'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'}), #Visto che è una FK faccio una select in base ai dipendenti registrati
            'organizers': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    