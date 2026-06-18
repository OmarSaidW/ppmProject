from django.contrib import admin
from .models import Event, Registration, Invitation # Assicurati di includere Invitation se serve

#Pagina di amministrazione del sito, qui puoi aggiungere, modificare o eliminare eventi, registrazioni o inviti
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'supervisor', 'date', 'location')
    search_fields = ('title', 'location')
    list_filter = ('date', 'supervisor')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'arrival_time', 'registration_date')

