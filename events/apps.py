from django.apps import AppConfig


class EventsConfig(AppConfig):
    name = 'events' #Registra l'app di Eventi per caricarla nel sistema

class UserConfig(AppConfig):
    name = 'users' 
    label = 'users'
