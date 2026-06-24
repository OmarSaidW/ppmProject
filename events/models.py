from django.db import models
from django.conf import settings
from django.urls import reverse
from datetime import datetime
"""
Le tabelle relazionali defite sono:
1. Event.supervisor -> (Uno-a-Molti) verso la tabella User.
2. Event.organizers -> (Molti-a-Molti) verso la tabella User.
3. Registration.event -> (Uno-a-Molti) che collega la registrazione all'evento.
4. Registration.attendee -> (Uno-a-Molti) che collega la registrazione all'utente partecipante.
5. Invitation.event -> (Uno-a-Molti) che collega l'invito all'evento.
6. Invitation.invitee -> (Uno-a-Molti) che collega l'invito all'utente invitato.
7. Invitation.inviter -> (Uno-a-Molti) che collega l'invito all'utente che ha inviato l'invito.
"""
#Nota: Le funzioni __str__ sono state generate con l'aiuto di AI, sono state inserite qui per chiarezza


class Event(models.Model):
    TIPO_CHOICES = [
        ('PUBLIC', 'Pubblico'),
        ('PRIVATE', 'Privato'),
    ]
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='PUBLIC')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_time_start = models.DateTimeField(default=datetime.now())
    date_time_end = models.DateTimeField(default= datetime(2026, 6, 30, 23, 47, 15))
    location = models.CharField(max_length=200)
    
    # Colleghiamo l'evento al nostro CustomUser tramite settings
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='supervised_events'
    )
    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='organized_events' 
    )
    stato = models.IntegerField(default=0)
    #Definita da ai per permettere di ritornare all'url del dettaglio evento
    #Utile per redirect
    def get_absolute_url(self):
        return reverse('dettaglio_evento', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title


class PublicEvent(Event):
    # Django crea automaticamente un OneToOneField event_ptr -> Event (PK condivisa)
    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )
    public_visibility = models.BooleanField(
        default=True
    )
    registration_required = models.BooleanField(
        default=True
    )
    max_participants = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Numero massimo di partecipanti (lasciare vuoto per illimitato)"
    )
    def __str__(self):
        return f"[Pubblico] {self.title}"    

class EventoPrivato(Event):

    invite_code = models.CharField(
        max_length=20,
        unique=True
    )

    invitation_deadline = models.DateTimeField()

    approval_required = models.BooleanField(
        default=False
    )

    secret_location = models.BooleanField(
        default=False
    )

class Registration(models.Model):
    STATO_CHOICES = [
        ('ATTIVO', 'Iscritto'),
        ('USCITO', 'Ha lasciato l\'evento'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    arrival_time = models.DateTimeField(null=True, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    # Permette all'attendee di "lasciare" l'evento mantenendo traccia nel DB
    stato = models.CharField(max_length=10, choices=STATO_CHOICES, default='ATTIVO')
    #Per Gestire il pagamento dell'evento pubblico :
    payment_status = models.CharField(
    max_length=20,
    choices=[
        ('PENDING', 'In attesa'), #Ovviamente non viene poi veramente gestito il pagamento dato 
        ('PAID', 'Pagato'),
        ('REFUNDED', 'Rimborsato'),
    ],
    default='PENDING'
)
    def __str__(self):
        return f"{self.user.username} - {self.event.title} [{self.stato}]"

class Invitation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invitations_received')
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invitations_sent')
    invited_at = models.DateTimeField(auto_now_add=True)
    # True se l'attendee ha rifiutato l'invito: il record rimane ma non appare nella lista attivi
    rifiutato = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'invitee')

    def __str__(self):
        stato = 'rifiutato' if self.rifiutato else 'attivo'
        return f"Invito ({stato}) per {self.invitee.username} a {self.event.title}"