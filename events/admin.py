from django.contrib import admin
from .models import Event, Registration, Invitation

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'title', 'supervisor', 'location', 'date_time_start', 'date_time_end')
    search_fields = ('title', 'location')
    list_filter = ('supervisor', 'tipo', 'date_time_start', 'date_time_end')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'arrival_time', 'registration_date', 'payment_status')

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('event', 'invitee', 'inviter', 'invited_at', 'rifiutato')

@admin.register(EventoPrivato)
class EventoPrivatoAdmin(admin.ModelAdmin):
    list_display = ('title', 'supervisor', 'location', 'date_time_start', 'date_time_end')
    search_fields = ('title', 'location')
    list_filter = ('supervisor', 'date_time_start', 'date_time_end')

@admin.register(PublicEvent)
class PublicEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'supervisor', 'location', 'date_time_start', 'date_time_end')
    search_fields = ('title', 'location')
    list_filter = ('supervisor', 'date_time_start', 'date_time_end')
