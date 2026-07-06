
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm, UserProfileUpdateForm, OrganizerChangeRoleForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.forms.utils import ErrorList
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from .models import CustomUser


class CustomLoginView(DjangoLoginView):
    template_name = 'registration/login.html'

    def form_invalid(self, form):
        username = form.data.get('username', '')
        try:
            user = CustomUser.objects.get(username=username)
            if user.ruolo == 'ORGANIZER' and not user.organizer_attivo:
                form._errors = {'__all__': ErrorList(['Utente Disattivato.'])}
                return self.render_to_response(self.get_context_data(form=form))
        except CustomUser.DoesNotExist:
            pass
        return super().form_invalid(form)


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/profilo.html'
    context_object_name = 'utente_profilo'

    #Funzioni base per visualizzare le mie iscrizioni a eventi con paginazione
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
            from django.core.paginator import Paginator
            from django.http import JsonResponse
            from django.db.models import Q
            from events.models import Event

            #Visualizza eventi passati e futuri in cui l'utente è organizzatore o supervisor o si è iscritto
            
            events = Event.objects.filter(
                Q(registration__user=self.object, registration__stato='ATTIVO') |
                Q(organizers=self.object) |
                Q(supervisor=self.object)
            ).distinct().order_by('-date_time_start')
            #Mi permette di caricare 30 eventi per pagina (cosi da non sovraccaricare la pagina)
            paginator = Paginator(events, 30)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            events_data = []
            for event in page_obj:
                events_data.append({
                    'id': event.id,
                    'title': event.title,
                    'date': event.date_time_start.strftime('%d/%m/%Y %H:%M') if event.date_time_start else '',
                    'location': event.location,
                    'url': event.get_absolute_url()
                })
            
            return JsonResponse({
                'events': events_data,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'number': page_obj.number,
                'num_pages': paginator.num_pages,
            })
        return super().get(request, *args, **kwargs)

class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/lista_utenti.html'
    context_object_name = 'utenti'

    def get_queryset(self):
        user = self.request.user
        qs = CustomUser.objects.all().order_by('username')
        if user.ruolo == 'ATTENDEE' and not user.is_superuser:
            return qs.filter(ruolo='ATTENDEE')
        ruolo_filter = self.request.GET.get('ruolo', '')
        if ruolo_filter in ('ORGANIZER', 'ATTENDEE'):
            qs = qs.filter(ruolo=ruolo_filter)
        return qs[:20]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ruolo_filter'] = self.request.GET.get('ruolo', '')
        return context


# --- UPDATE: Cambia Ruolo (FIX: messages.success in form_valid) ---
class OrganizerUpdateUserView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = OrganizerChangeRoleForm # Usa il form che modifica SOLO il ruolo
    template_name = 'users/organizer_modifica_utente.html'

    def test_func(self):
        # Solo gli Organizer o i Superuser possono accedere
        return self.request.user.ruolo == 'ORGANIZER' or self.request.user.is_superuser

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Ruolo di {self.object.username} aggiornato con successo!")
        return response

    def get_success_url(self):
        return reverse_lazy('lista_utenti')


# --- UPDATE: Modifica Profilo ---
class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileUpdateForm  # Modifica solo email e telefono
    template_name = 'users/modifica_profilo.html'

    def test_func(self):
        return self.request.user == self.get_object()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Profilo aggiornato con successo!")
        return response

    def get_success_url(self):
        return reverse_lazy('dettaglio_profilo', kwargs={'pk': self.object.pk})

# --- ELIMINA ACCOUNT ---
class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CustomUser
    template_name = 'users/elimina_profilo.html'
    success_url = reverse_lazy('lista_eventi')

    def test_func(self):
        user = self.request.user
        return user == self.get_object() and user.ruolo == 'ATTENDEE' and not user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, "Il tuo account è stato eliminato.")
        return super().form_valid(form)


# --- DELETE: Admin/Organizer elimina un altro utente (solo ATTENDEE) ---
class AdminDeleteUserView(LoginRequiredMixin, View):
    def post(self, request, pk):
        target = get_object_or_404(CustomUser, pk=pk)

        if target == request.user:
            messages.error(request, "Non puoi eliminare te stesso.")
            return redirect('lista_utenti')

        if target.is_superuser:
            messages.error(request, "Non puoi eliminare un amministratore di sistema.")
            return redirect('lista_utenti')

        if target.ruolo != 'ATTENDEE':
            messages.error(request, "È possibile eliminare solo account di tipo Attendee.")
            return redirect('lista_utenti')

        if request.user.ruolo != 'ORGANIZER' and not request.user.is_superuser:
            messages.error(request, "Non hai i permessi per eliminare utenti.")
            return redirect('lista_utenti')

        username = target.username
        target.delete()
        messages.success(request, f"Account di {username} eliminato con successo.")
        return redirect('lista_utenti')


# --- TOGGLE stato organizer (solo superuser) ---
class ToggleOrganizerStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_superuser:
            messages.error(request, "Solo l'amministratore può modificare lo stato degli organizzatori.")
            return redirect('lista_utenti')

        target = get_object_or_404(CustomUser, pk=pk, ruolo='ORGANIZER')
        target.organizer_attivo = not target.organizer_attivo
        target.is_active = target.organizer_attivo
        target.save(update_fields=['organizer_attivo', 'is_active'])
        stato = "attivato" if target.organizer_attivo else "disattivato"
        messages.success(request, f"Organizzatore {target.username} {stato}.")
        return redirect('lista_utenti')