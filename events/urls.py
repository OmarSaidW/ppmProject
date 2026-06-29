from django.urls import path
from .views import (
    EventListView, EventDetailView, DeleteEventView,
    JoinEventView, LeaveEventView, InviteUserView, DeleteInvitationView,
    RifiutaInvitoView, RemoveParticipantView, RemoveOrganizerView,
    EventCalendarJsonView,
    EventTypeSelectorView, PublicEventCreateView, PrivateEventCreateView,
    PublicEventUpdateView, PrivateEventUpdateView,
    PaymentView,
)


urlpatterns = [
    # Lista eventi
    path('', EventListView.as_view(), name='lista_eventi'),

    # Creazione evento (scegli tipo → crea specifico)
    path('crea/', EventTypeSelectorView.as_view(), name='crea_evento'),
    path('crea/pubblico/', PublicEventCreateView.as_view(), name='crea_evento_pubblico'),
    path('crea/privato/', PrivateEventCreateView.as_view(), name='crea_evento_privato'),

    # Dettaglio evento
    path('<int:pk>/', EventDetailView.as_view(), name='dettaglio_evento'),

    # Azioni sull'evento (POST only)
    path('<int:pk>/elimina/', DeleteEventView.as_view(), name='elimina_evento'),
    path('<int:pk>/unisciti/', JoinEventView.as_view(), name='unisciti_evento'),
    path('<int:pk>/lascia/', LeaveEventView.as_view(), name='lascia_evento'),
    path('<int:pk>/modifica_evento_pubblico/', PublicEventUpdateView.as_view() , name='modifica_evento_pubblico'),
    path('<int:pk>/modifica_evento_privato/', PrivateEventUpdateView.as_view() , name='modifica_evento_privato'),

    # Inviti
    path('<int:pk>/invita/', InviteUserView.as_view(), name='invita_utente'),
    path('<int:pk>/invito/<int:invito_pk>/elimina/', DeleteInvitationView.as_view(), name='elimina_invito'),
    path('<int:pk>/invito/rifiuta/', RifiutaInvitoView.as_view(), name='rifiuta_invito'),

    # Pagamento biglietto
    path('<int:pk>/pagamento/', PaymentView.as_view(), name='pagamento_evento'),

    # Partecipanti e organizzatori
    path('<int:pk>/partecipante/<int:reg_pk>/rimuovi/', RemoveParticipantView.as_view(), name='rimuovi_partecipante'),
    path('<int:pk>/organizzatore/<int:user_pk>/rimuovi/', RemoveOrganizerView.as_view(), name='rimuovi_organizzatore'),

    # Calendario JSON feed
    path('calendario/json/', EventCalendarJsonView.as_view(), name='eventi_json'),
]
