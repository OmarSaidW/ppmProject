from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    """
    Estendiamo il UserAdmin standard per mostrare i campi personalizzati
    (ruolo e telefono) nel pannello di controllo.
    """
    # 1. Mostra i campi nella lista di riepilogo degli utenti
    list_display = ('username', 'email', 'ruolo', 'is_staff')
    
    # 2. Aggiunge i campi nella pagina di MODIFICA dell'utente
    fieldsets = UserAdmin.fieldsets + (
        ('Informazioni di Ruolo (Esame)', {'fields': ('ruolo', 'telefono')}),
    )
    
    # 3. Aggiunge i campi nella pagina di CREAZIONE di un nuovo utente
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informazioni di Ruolo (Esame)', {'fields': ('ruolo', 'telefono')}),
    )

# Registriamo il CustomUser con la nostra classe CustomUserAdmin avanzata
admin.site.register(CustomUser, CustomUserAdmin)