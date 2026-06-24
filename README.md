## Event Manager
Sistema di gestione eventi che permette di creare, invitare, iscriversi e partecipare agli eventi. Costrito come Web App 
sul framework Django (https://www.djangoproject.com/). 
Il sistema presenta 2 tipologie di utenti: 
- ORGANIZER
- ATTENDEE

Inoltre è stato implementato un sistema di Admin personalizzato che ha la possibilità di svolgere tutte le operazioni
permettendo cosi ad un amministratore di sistema di gestire l'intero sistema.
 
Il progetto è diviso in due applicazioni (separazione dei compiti): 
1. users: Gestisce gli utenti del sistema e le loro interazioni
2. events: Gestisce gli eventi del sistema e le loro interazioni

Utente: 
Gli utente sono raggrupati in due categorie:
- ORGANIZER: 
    - Possono creare eventi
    - Possono invitare altri utenti (ATTENDEE e ORGANIZER) a partecipare agli eventi
    - Possono essere supervisor di eventi (anche non creati da loro)
    - Possono iscriversi agli eventi
    - Possono partecipare agli eventi
    - Possono visualizzare gli eventi
    - Possono modificare eventi (solo quelli di cui sono organizzatori)
    - Possono eliminare eventi (solo quelli di cui sono organizzatori)
- ATTENDEE: 
    - Possono iscriversi agli eventi (se invitati)
    - Possono visualizzare gli eventi (se invitati o iscritti)




EventS:
Due tipi di evento: 
- Pubblico: Possono essere visti da tutti gli utenti
- Privato: Possono essere visti solo dagli utenti invitati

    