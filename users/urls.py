from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    SignUpView,
    UserListView,
    UserDetailView,
    UserUpdateView,
    OrganizerUpdateUserView,
    UserDeleteView,
    AdminDeleteUserView,
)

urlpatterns = [
    # Autenticazione
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),

    # Registrazione
    path('signup/', SignUpView.as_view(), name='signup'),

    # Utenti
    path('lista/', UserListView.as_view(), name='lista_utenti'),
    path('<int:pk>/', UserDetailView.as_view(), name='dettaglio_profilo'),
    path('<int:pk>/modifica/', UserUpdateView.as_view(), name='modifica_profilo'),
    path('<int:pk>/cambia-ruolo/', OrganizerUpdateUserView.as_view(), name='organizer_modifica_utente'),
    path('<int:pk>/elimina/', UserDeleteView.as_view(), name='elimina_profilo'),
    path('<int:pk>/admin-elimina/', AdminDeleteUserView.as_view(), name='admin_elimina_utente'),
]