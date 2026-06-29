from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from .models import Event, PublicEvent, EventoPrivato, Registration, Invitation
from .forms import PublicEventForm, EventoPrivatoForm

CustomUser = get_user_model()


# --- LISTA EVENTI ---
class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/lista_eventi.html'
    context_object_name = 'eventi'

    def get_queryset(self):
        user = self.request.user
        if user.ruolo == 'ORGANIZER' or user.is_superuser:
            qs = Event.objects.all()
        else:
            qs = Event.objects.filter(
                Q(registration__user=user) |
                Q(invitations__invitee=user) |
                Q(publicevent__public_visibility=True)
            ).distinct()
        return qs.order_by('-date_time_start')[:50]


# --- DETTAGLIO EVENTO ---
class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'events/dettaglio_evento.html'
    context_object_name = 'evento'

    def test_func(self):
        user = self.request.user
        if user.ruolo == 'ORGANIZER' or user.is_superuser:
            return True
        event = self.get_object()
        try:
            if event.publicevent.public_visibility:
                return True
        except PublicEvent.DoesNotExist:
            pass
        has_registration = Registration.objects.filter(user=user, event=event).exists()
        has_invitation = Invitation.objects.filter(invitee=user, event=event).exists()
        return has_registration or has_invitation

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

        try:
            context['public_event'] = event.publicevent
            context['modifica_url'] = reverse('modifica_evento_pubblico', kwargs={'pk': event.pk})
        except PublicEvent.DoesNotExist:
            context['public_event'] = None
            try:
                event.eventoprivato
                context['modifica_url'] = reverse('modifica_evento_privato', kwargs={'pk': event.pk})
            except EventoPrivato.DoesNotExist:
                context['modifica_url'] = None

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
            try:
                public_event = event.publicevent
            except PublicEvent.DoesNotExist:
                public_event = None

            has_invitation = Invitation.objects.filter(invitee=user, event=event, rifiutato=False).exists()
            is_public_open = public_event is not None and public_event.public_visibility

            if not has_invitation and not is_public_open:
                messages.error(request, "Non hai un invito attivo per questo evento.")
                return redirect('dettaglio_evento', pk=pk)

            if public_event and public_event.max_participants:
                current_count = Registration.objects.filter(event=event, stato='ATTIVO').count()
                if current_count >= public_event.max_participants:
                    messages.error(request, "L'evento ha raggiunto il numero massimo di partecipanti.")
                    return redirect('dettaglio_evento', pk=pk)

            if public_event and public_event.ticket_price > 0:
                return redirect('pagamento_evento', pk=pk)

            reg, created = Registration.objects.get_or_create(
                user=user, event=event,
                defaults={'stato': 'ATTIVO', 'payment_status': 'PAID'}
            )
            if not created and reg.stato == 'USCITO':
                reg.stato = 'ATTIVO'
                reg.save()
                messages.success(request, "Ti sei re-iscritto a questo evento!")
            elif created:
                messages.success(request, "Ti sei iscritto con successo a questo evento!")
            else:
                messages.info(request, "Sei già iscritto a questo evento.")

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


# --- SCELTA TIPO EVENTO ---
class EventTypeSelectorView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'events/scegli_tipo_evento.html'

    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser


# --- CREA EVENTO PUBBLICO ---
class PublicEventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PublicEvent
    form_class = PublicEventForm
    template_name = 'events/crea_evento.html'
    success_url = reverse_lazy('lista_eventi')

    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.tipo = 'PUBLIC'
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_evento'] = 'Pubblico'
        return context


# --- CREA EVENTO PRIVATO ---
class PrivateEventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = EventoPrivato
    form_class = EventoPrivatoForm
    template_name = 'events/crea_evento.html'
    success_url = reverse_lazy('lista_eventi')

    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.tipo = 'PRIVATE'
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_evento'] = 'Privato'
        return context


# --- MODIFICARE UN EVENTO ---
class PrivateEventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EventoPrivato
    form_class = EventoPrivatoForm
    template_name = 'events/modifica_evento_privato.html'
    success_url = reverse_lazy('lista_eventi')

    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, pk=self.kwargs['pk'])
        try:
            return event.eventoprivato
        except EventoPrivato.DoesNotExist:
            from django.http import Http404
            raise Http404("Evento privato non trovato.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_evento'] = 'Privato'
        return context


class PublicEventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PublicEvent
    form_class = PublicEventForm
    template_name = 'events/modifica_evento_pubblico.html'
    success_url = reverse_lazy('lista_eventi')

    def test_func(self):
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, pk=self.kwargs['pk'])
        try:
            return event.publicevent
        except PublicEvent.DoesNotExist:
            # Event created before MTI refactor: auto-create missing child row
            pub = PublicEvent(
                event_ptr_id=event.pk,
                ticket_price=0,
                public_visibility=True,
                registration_required=True,
                max_participants=None,
            )
            pub.save_base(raw=True)
            event.tipo = 'PUBLIC'
            event.save(update_fields=['tipo'])
            return PublicEvent.objects.get(pk=event.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_evento'] = 'Pubblico'
        return context


# --- PAGAMENTO BIGLIETTO ---
class PaymentView(LoginRequiredMixin, View):
    def get(self, request, pk):
        event = get_object_or_404(PublicEvent, pk=pk)
        if request.user.ruolo != 'ATTENDEE':
            messages.error(request, "Solo gli attendee possono acquistare biglietti.")
            return redirect('dettaglio_evento', pk=pk)
        if Registration.objects.filter(user=request.user, event=event, stato='ATTIVO').exists():
            messages.info(request, "Sei già iscritto a questo evento.")
            return redirect('dettaglio_evento', pk=pk)
        return render(request, 'events/pagamento.html', {'evento': event})

    def post(self, request, pk):
        event = get_object_or_404(PublicEvent, pk=pk)
        user = request.user
        if user.ruolo != 'ATTENDEE':
            messages.error(request, "Solo gli attendee possono acquistare biglietti.")
            return redirect('dettaglio_evento', pk=pk)

        with transaction.atomic():
            if event.max_participants:
                current_count = Registration.objects.select_for_update().filter(
                    event=event, stato='ATTIVO'
                ).count()
                if current_count >= event.max_participants:
                    messages.error(request, "L'evento ha raggiunto il numero massimo di partecipanti.")
                    return redirect('dettaglio_evento', pk=pk)

            reg, created = Registration.objects.get_or_create(
                user=user,
                event=event,
                defaults={'stato': 'ATTIVO', 'payment_status': 'PAID'}
            )
            if not created:
                if reg.stato == 'USCITO':
                    reg.stato = 'ATTIVO'
                    reg.payment_status = 'PAID'
                    reg.save()
                    messages.success(request, f"Pagamento di €{event.ticket_price:.2f} completato! Ti sei re-iscritto all'evento.")
                else:
                    messages.info(request, "Sei già iscritto a questo evento.")
            else:
                messages.success(request, f"Pagamento di €{event.ticket_price:.2f} completato! Sei iscritto all'evento.")

        return redirect('dettaglio_evento', pk=pk)


# --- CALENDARIO EVENTI (JSON per FullCalendar) ---
class EventCalendarJsonView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        from django.utils import timezone
        import datetime
        now = timezone.now()
        six_months_ago = now - datetime.timedelta(days=180)
        six_months_later = now + datetime.timedelta(days=180)

        if user.ruolo == 'ORGANIZER' or user.is_superuser:
            eventi = Event.objects.filter(date_time_start__range=(six_months_ago, six_months_later))
        else:
            eventi = Event.objects.filter(
                Q(registration__user=user) |
                Q(invitations__invitee=user) |
                Q(publicevent__public_visibility=True)
            ).filter(date_time_start__range=(six_months_ago, six_months_later)).distinct()

        data = []
        for e in eventi:
            data.append({
                'id': e.pk,
                'title': e.title,
                'start': e.date_time_start.isoformat(),
                'url': e.get_absolute_url(),
                'extendedProps': {'location': e.location},
            })
        return JsonResponse(data, safe=False)
