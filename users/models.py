from django.db import models
from django.contrib.auth.models import AbstractUser, Group

#Modello Uente personalizzato che estende AbstractUser (come richiesto)
class CustomUser(AbstractUser):
    #Definiamo i ruoli che l'utente può avere (due: organizzatore e partecipante , default: partecipante)
    RUOLO_CHOICES = [
        ('ORGANIZER', 'Organizzatore'),
        ('ATTENDEE', 'Partecipante'),
    ] 
    #Nota: Non possiamo definire la relazione con il gruppo qui, perché il gruppo non esiste ancora al momento della creazione dell'utente
    ruolo = models.CharField(max_length=20, choices=RUOLO_CHOICES, default='ATTENDEE')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    organizer_attivo = models.BooleanField(default=True)
    #TODO: inserire una foto profilo
    #foto_profilo = models.ImageField(upload_to='foto_profilo/', blank=True, null=True) 

    def save(self, *args, **kwargs):
        # 1. Salva l'utente nel database
        super().save(*args, **kwargs)
        
        # 2. Logica di automazione dei Gruppi richiesta dall'esame
        if self.ruolo == 'ORGANIZER':
            gruppo, _ = Group.objects.get_or_create(name='Organizers')
            self.groups.add(gruppo)
        elif self.ruolo == 'ATTENDEE':
            gruppo, _ = Group.objects.get_or_create(name='Attendees')
            self.groups.add(gruppo)