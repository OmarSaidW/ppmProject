from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Exists, OuterRef
from .models import Event, Registration, Invitation
from .forms import EventForm, EventUpdateForm

# Recuperiamo il modello utente personalizzato in modo sicuro per Django
CustomUser = get_user_model()

# --- LISTA EVENTI ---
class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/lista_eventi.html'
    context_object_name = 'eventi'

    def get_queryset(self):
        user = self.request.user
        if user.ruolo == 'ORGANIZER' or user.is_superuser: 
            #Se è organizzatore o superAdmin deve (per logica ) vedere tutti gli eventi
            qs = Event.objects.all()
        else:
            qs = Event.objects.filter( 
                #Altrimenti (Attendee) vede solo gli eventi a cui è iscritto o invitato
                Q(registration__user=user) | Q(invitations__invitee=user)
            ).distinct()
        return qs.order_by('-date')[:50]
        # Serve per limitare il numero di eventi visualizzati per volta

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EventForm()
        return context


# --- DETTAGLIO EVENTO ---
#Forse la classe più completa finora visto che contiene logica di controllo per tutti e tre ruoli
#Inoltre gestisce molto bene i template, permettendo di mostrare diversi bottoni

class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'events/dettaglio_evento.html'
    context_object_name = 'evento'
    #Organizer e super admin possono vedere tutto, attendee solo se invitato
    def test_func(self):
        user = self.request.user
        if user.ruolo == 'ORGANIZER' or user.is_superuser:
            return True
        event = self.get_object()
        has_registration = Registration.objects.filter(user=user, event=event).exists()
        has_invitation = Invitation.objects.filter(invitee=user, event=event).exists()
        return has_registration or has_invitation

    #Funzioni che viene chiamata prima di renderizzare il template (come in List View)
    def _context_per_organizer(self, event, is_supervisor):
        accepted_reg = Registration.objects.filter(
            user=OuterRef('invitee'), event=OuterRef('event'), stato='ATTIVO'
        )
        ctx = {
            'inviti': event.invitations.filter(rifiutato=False).annotate(
                accettato=Exists(accepted_reg)
            ).select_related('invitee', 'inviter'),
            'invitabili': CustomUser.objects.filter(ruolo='ATTENDEE').exclude(
                invitations_received__event=event
            ).exclude(
                registration__event=event
            ),
            'organizzatori': event.organizers.all(),
        }
        if is_supervisor:
            ctx['inviti_rifiutati'] = event.invitations.filter(
                rifiutato=True
            ).select_related('invitee')
        return ctx
 
    def _context_per_attendee(self, event, user):
        try:
            mio_invito = Invitation.objects.get(invitee=user, event=event, rifiutato=False)
        except Invitation.DoesNotExist:
            mio_invito = None
        try:
            mia_registrazione = Registration.objects.get(user=user, event=event, stato='ATTIVO')
        except Registration.DoesNotExist:
            mia_registrazione = None
        return {
            'mio_invito': mio_invito,
            'mia_registrazione': mia_registrazione,
        }
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        user = self.request.user
 
        is_supervisor = (user == event.supervisor) or user.is_superuser
        context['is_supervisor'] = is_supervisor
 
        context['partecipanti'] = Registration.objects.filter(
            event=event, stato='ATTIVO'
        ).select_related('user')
        context['usciti'] = Registration.objects.filter(
            event=event, stato='USCITO'
        ).select_related('user')
 
        if user.ruolo == 'ORGANIZER' or user.is_superuser:
            context['user_is_joined'] = (
                user == event.supervisor or event.organizers.filter(id=user.id).exists()
            )
            context.update(self._context_per_organizer(event, is_supervisor))
        else:
            context['user_is_joined'] = Registration.objects.filter(
                user=user, event=event, stato='ATTIVO'
            ).exists()
            context.update(self._context_per_attendee(event, user))
 
        return context


# --- UNIRSI A UN EVENTO ---
class JoinEventView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        user = request.user

        if user.ruolo == 'ORGANIZER' or user.is_superuser:
            if user != event.supervisor and not event.organizers.filter(id=user.id).exists():
                event.organizers.add(user)
                messages.success(request, "Ti sei unito al team degli organizzatori per questo evento!")
            else:
                messages.info(request, "Fai già parte del team degli organizzatori di questo evento.")
        elif user.ruolo == 'ATTENDEE':
            has_invitation = Invitation.objects.filter(invitee=user, event=event, rifiutato=False).exists()
            if has_invitation:
                reg, created = Registration.objects.get_or_create(user=user, event=event, defaults={'stato': 'ATTIVO'})
                if not created and reg.stato == 'USCITO':
                    reg.stato = 'ATTIVO'
                    reg.save()
                    messages.success(request, "Ti sei re-iscritto a questo evento!")
                elif created:
                    messages.success(request, "Ti sei iscritto con successo a questo evento!")
                else:
                    messages.info(request, "Sei già iscritto a questo evento.")
            else:
                messages.error(request, "Non hai un invito attivo per questo evento.")

        return redirect('dettaglio_evento', pk=pk)


# --- LASCIARE UN EVENTO ---
class LeaveEventView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        reg = get_object_or_404(Registration, user=request.user, event=event)
        reg.stato = 'USCITO'
        reg.save()
        messages.success(request, "Hai lasciato l'evento.")
        return redirect('dettaglio_evento', pk=pk)


# --- RIFIUTARE UN INVITO ---
class RifiutaInvitoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        invito = get_object_or_404(Invitation, invitee=request.user, event=event)
        invito.rifiutato = True
        invito.save()
        messages.success(request, f"Hai rifiutato l'invito per '{event.title}'.")
        return redirect('lista_eventi')


# --- ELIMINARE UN INVITO ---
class DeleteInvitationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def post(self, request, pk, invito_pk):
        event = get_object_or_404(Event, pk=pk)
        invito = get_object_or_404(Invitation, pk=invito_pk, event=event)
        nome = invito.invitee.username
        invito.delete()
        messages.success(request, f"Invito per {nome} eliminato.")
        return redirect('dettaglio_evento', pk=pk)


# --- RIMUOVERE UN PARTECIPANTE ---
class RemoveParticipantView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def post(self, request, pk, reg_pk):
        event = get_object_or_404(Event, pk=pk)
        reg = get_object_or_404(Registration, pk=reg_pk, event=event)
        nome = reg.user.username
        utente = reg.user
        reg.delete()
        Invitation.objects.filter(invitee=utente, event=event).delete()
        messages.success(request, f"Partecipante {nome} rimosso dall'evento (invito eliminato).")
        return redirect('dettaglio_evento', pk=pk)


# --- RIMUOVERE UN ORGANIZZATORE ---
class RemoveOrganizerView(LoginRequiredMixin, View):
    def post(self, request, pk, user_pk):
        event = get_object_or_404(Event, pk=pk)
        if request.user != event.supervisor and not request.user.is_superuser:
            messages.error(request, "Non hai i permessi per rimuovere organizzatori.")
            return redirect('dettaglio_evento', pk=pk)
        organizer = get_object_or_404(CustomUser, pk=user_pk)
        event.organizers.remove(organizer)
        messages.success(request, f"Organizzatore {organizer.username} rimosso dall'evento.")
        return redirect('dettaglio_evento', pk=pk)


# --- ELIMINARE UN EVENTO ---
class DeleteEventView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if request.user != event.supervisor and not request.user.is_superuser:
            messages.error(request, "Solo il supervisor può eliminare questo evento.")
            return redirect('dettaglio_evento', pk=pk)
        event.delete()
        messages.success(request, "Evento eliminato con successo.")
        return redirect('lista_eventi')


# --- INVITARE UN UTENTE ---
class InviteUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        invitee_id = request.POST.get('invitee_id')
        if invitee_id:
            invitee = get_object_or_404(CustomUser, id=invitee_id)
            if invitee.ruolo == 'ATTENDEE':
                Invitation.objects.get_or_create(
                    event=event,
                    invitee=invitee,
                    defaults={'inviter': request.user}
                )
                messages.success(request, f"Utente {invitee.username} invitato con successo!")
            else:
                messages.error(request, "Puoi invitare solo partecipanti (Attendee).")
        return redirect('dettaglio_evento', pk=pk)


# --- CREARE UN EVENTO ---
class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/crea_evento.html'
    success_url = reverse_lazy('lista_eventi')

    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser


# --- MODIFICARE UN EVENTO ---
class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventUpdateForm
    template_name = 'events/modifica_evento.html'

    def get_success_url(self):
        messages.success(self.request, "Evento modificato con successo!")
        return reverse_lazy('dettaglio_evento', kwargs={'pk': self.object.pk})

    def test_func(self):
        event = self.get_object()
        user = self.request.user
        is_organizer = event.organizers.filter(id=user.id).exists()
        is_supervisor = event.supervisor == user
        return is_supervisor or is_organizer or user.is_superuser





# --- CALENDARIO EVENTI (JSON per FullCalendar) ---
class EventCalendarJsonView(LoginRequiredMixin, View):
    #carica 6 mesi passati e 6 mesi futuri
    def get(self, request):
        user = request.user
        from django.utils import timezone
        import datetime
        now = timezone.now()
        six_months_ago = now - datetime.timedelta(days=180)
        six_months_later = now + datetime.timedelta(days=180)

        if user.ruolo == 'ORGANIZER' or user.is_superuser:
            eventi = Event.objects.filter(date__range=(six_months_ago, six_months_later))
        else:
            eventi = Event.objects.filter(
                Q(registration__user=user) | Q(invitations__invitee=user)
            ).filter(date__range=(six_months_ago, six_months_later)).distinct()

        data = []
        for e in eventi:
            data.append({
                'id': e.pk,
                'title': e.title,
                'start': e.date.isoformat(),
                'url': e.get_absolute_url(),
                'extendedProps': {'location': e.location},
            })
        return JsonResponse(data, safe=False)
