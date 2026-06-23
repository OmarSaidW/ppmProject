
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import CustomUserCreationForm, UserProfileUpdateForm, OrganizerChangeRoleForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from .models import CustomUser

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

@login_required
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
            ).distinct().order_by('-date')
            #Mi permette di caricare 30 eventi per pagina (cosi da non sovraccaricare la pagina)
            paginator = Paginator(events, 30)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            events_data = []
            for event in page_obj:
                events_data.append({
                    'id': event.id,
                    'title': event.title,
                    'date': event.date.strftime('%d/%m/%Y %H:%M') if event.date else '',
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

@login_required
class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/lista_utenti.html'
    context_object_name = 'utenti'


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
@login_required
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
        return self.request.user == self.get_object()

    def form_valid(self, form):
        messages.success(self.request, "Il tuo account è stato eliminato.")
        return super().form_valid(form)


# --- DELETE: Admin/Organizer elimina un altro utente ---
class AdminDeleteUserView(LoginRequiredMixin, View):
    def post(self, request, pk):
        target = get_object_or_404(CustomUser, pk=pk)

        # Non si può eliminare se stessi
        if target == request.user:
            messages.error(request, "Non puoi eliminare te stesso.")
            return redirect('lista_utenti')

        # Non si può eliminare un superuser
        if target.is_superuser:
            messages.error(request, "Non puoi eliminare un amministratore di sistema.")
            return redirect('lista_utenti')

        # Organizer → può eliminare solo ATTENDEE
        if request.user.ruolo == 'ORGANIZER' and not request.user.is_superuser:
            if target.ruolo != 'ATTENDEE':
                messages.error(request, "Come Organizer puoi eliminare solo account Attendee.")
                return redirect('lista_utenti')

        # Superuser → può eliminare ATTENDEE e ORGANIZER (non altri superuser)
        elif not request.user.is_superuser:
            messages.error(request, "Non hai i permessi per eliminare utenti.")
            return redirect('lista_utenti')

        username = target.username
        target.delete()
        messages.success(request, f"Account di {username} eliminato con successo.")
        return redirect('lista_utenti')