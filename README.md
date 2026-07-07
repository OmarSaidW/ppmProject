# Event Management System

**Studente:** Omar Said  
**Tipo progetto:** Full-Stack Web Application  
**Framework:** Django
**Tipo di Elaborato**  Traccia 3: Event Management System  
**Link al deploy**  https://ppmproject-cmfb.onrender.com


---

## Breve Descrizione

Questa è un'applicazione web completa per la gestione di eventi pubblici e privati (Event Management System UNIFI). 

Il sistema supporta tre ruoli distinti (Superadmin, Organizer, Attendee) con permessi diversi (personalizzati) su ogni operazione. Gli organizzatori creano e gestiscono eventi, gli attendee si iscrivono o accettano inviti, il superadmin ha controllo totale sull'utenza. 
Tutte le pagine sono accessibili solo dopo autenticazione. E' possibile registrarsi al sito tramite un form di registrazione separato (sotto forma di attendee). 

Gli eventi seguono un modello a ereditarietà multi-tabella (MTI) Django:  
`Event` → `PublicEvent` | `EventoPrivato`

Lo stato di ogni evento (`PROGRAMMATO` / `IN_CORSO` / `PASSATO`) è calcolato dinamicamente a runtime confrontando `date_time_start`/`date_time_end` con `timezone.now()`, senza campo persistente.

---

## Funzionalità per ruolo

### Superadmin (Forma Speciale di Organizer)
- Accesso all'interfaccia di amministrazione Django (`/admin/`) -> Personalizzata
- Attivazione/disattivazione di account Organizer (blocca il login quando disattivato con messaggio specifico "Utente Disattivato")
- Eliminazione di account Attendee dalla lista utenti
- Cambio ruolo di qualsiasi utente 
- "Tutte le funzionalità di Organizer"

### Organizer
- Creazione di eventi pubblici (`PublicEvent`) e privati (`EventoPrivato`)
- Modifica e cancellazione dei propri eventi
- Invito di utenti Attendee a eventi privati tramite ricerca username
- Rimozione di partecipanti e co-organizzatori da un evento
- Visualizzazione lista completa partecipanti
- Cambio ruolo di utenti Attendee (da Attendee a Organizer)

### Attendee
- Visualizzazione eventi pubblici con `public_visibility=True`
- Iscrizione ad eventi pubblici (con pagamento simulato se `ticket_price > 0`) implentato con transaction.atomic()
- Ricezione e gestione inviti ad eventi privati (accetta / rifiuta)
- Abbandono di un evento a cui si è iscritti
- Location nascosta fino all'iscrizione se `secret_location=True`
- Visibilità limitata nella lista utenti (vede solo altri Attendee, non gli Organizer)
- Eliminazione del proprio account

### Tutti gli utenti autenticati
- Calendario dinamico degli eventi (FullCalendar, feed JSON su `/eventi/calendario/json/`) -> Implementato con "SignalR"
- Pagina di profilo personale con lista eventi in cui si è "organizzatore" o "partecipante" (quindi lista unificata) paginata
- Modifica del proprio profilo (email, telefono)


---

## Architettura

### Struttura app


ppmProject contiene tre sottodirectory:
-  users/          # autenticazione, CustomUser, ruoli, gestione account
- events/         # eventi, iscrizioni, inviti, calendario
- ppmProject/     # config (asgi, settings, urls, wsgi)

### Architettura Frontend

Il frontend è creato usando il template engine di Django. I template estendono `events/base.html` tramite blocchi (`{% block content %}`). Lo stile si basa su Bootstrap 5.3.3 e Bootstrap Icons, con un CSS personalizzato (non sono state usate librerie come Tailwind) in `events/static/events/css/style.css`. JavaScript gestisce interazioni con il browser e comunica con il backend. Viene usata per: 
- Far sparire automaticamente i messaggi
- Sincronizzazione tra checkbox e select per la selezione organizzatori (prima la selezione era effettuata solo tramite select e quindi poco pratica)
- calendario dinamico

### Modelli principali

```
CustomUser(AbstractUser) -> Derivato da AbstractUser di Django
   -> ruolo: CharField [ORGANIZER | ATTENDEE]
   -> telefono: CharField
   -> organizer_attivo: BooleanField     # Necessario per bloccare l'organizzatore 

Event  (tabella base MTI) -> E' stata utilizzata l'Ereditarietà Multi-Tabella di Django
   -> title, description, location
   -> date_time_start, date_time_end
   -> supervisor: è una FK a CustomUser
   -> organizers: è una FK Molti a Molti verso CustomUser
   -> tipo: CharField (PUBLIC,  PRIVATE)
   -> stato_evento: (ROGRAMMATO, IN_CORSO, PASSATO)

PublicEvent(Event)  -> tabella: events_publicevent -> Estende Event
  -> ticket_price: Decimal
  -> public_visibility: Boolean
  -> registration_required: Boolean
  -> max_participants: PositiveInteger (nullable = illimitato)

EventoPrivato(Event) -> tabella: events_eventoprivato -> Estende Event
  -> invite_code: CharField (unique)
  -> invitation_deadline: DateTimeField
  -> approval_required: Boolean
  -> secret_location: Boolean

Registration -> Modello per gestire le iscrizioni degli attendee agli eventi
  -> user: è una FK a CustomUser
  -> event: è una FK a Event
  -> stato: CharField [ATTIVO | USCITO]
  -> payment_status: CharField [PENDING | PAID | REFUNDED]

Invitation -> Modello per gestire gli inviti degli organizer agli attendee agli eventi che la richiedono
  -> event: è una FK a Event
  -> invitee: è una FK a CustomUser
  -> inviter: è una FK a CustomUser
  -> rifiutato: è un Boolean
```

### Relazioni tra tabelle

| Tipo | Da | A |
|------|----|---|
| FK (uno-a-molti) | `Event.supervisor` | `CustomUser` |
| M2M | `Event.organizers` | `CustomUser` |
| FK (uno-a-molti) | `Registration.user` | `CustomUser` |
| FK (uno-a-molti) | `Registration.event` | `Event` |
| FK (uno-a-molti) | `Invitation.invitee` | `CustomUser` |
| FK (uno-a-molti) | `Invitation.inviter` | `CustomUser` |
| FK (uno-a-molti) | `Invitation.event` | `Event` |
| OneToOne (Ereditarietà Multi-Tabella) | `PublicEvent.event_ptr` | `Event` |
| OneToOne (Ereditarietà Multi-Tabella) | `EventoPrivato.event_ptr` | `Event` |

### Views principali

| View | Classe base | Accesso |
|------|-------------|---------|
| `EventListView` | `ListView` | Tutti |
| `EventDetailView` | `UserPassesTestMixin, DetailView` | Tutti (con controllo) |
| `PublicEventCreateView` | `UserPassesTestMixin, CreateView` | Solo Organizer |
| `PrivateEventCreateView` | `UserPassesTestMixin, CreateView` | Solo Organizer |
| `PublicEventUpdateView` | `UserPassesTestMixin, UpdateView` | Solo Organizer proprietario |
| `PrivateEventUpdateView` | `UserPassesTestMixin, UpdateView` | Solo Organizer proprietario |
| `JoinEventView` | `View` | Solo Attendee |
| `PaymentView` | `View` | Solo Attendee |
| `EventCalendarJsonView` | `View` | Tutti |
| `UserListView` | `ListView` | Tutti (filtrata per ruolo) |
| `CustomLoginView` | `DjangoLoginView` | Pubblico |
| `ToggleOrganizerStatusView` | `View` | Solo Superadmin |

> **Nota**: Per velocizzare la scrittura è stato omesso il `LoginRequiredMixin` su tutte le viste nella tabella. 
> In realtà è stato aggiunto a tutte le viste eccezzione fatta per `CustomLoginView`

## Scelte Architetturali
Sono state fatte scelte di implementazione per gestione di eventi e utenti. 
### Gestione CRUD
La gestione CRUD non è stata implementata completamente per tutte le tabelle: 
- Gli `Organizer` non possono essere eliminati ma solo disattivati. 
- Gli `eventi` non possono essere passati da `Privato` a `Pubblico` o viceversa. 
- Per il resto è stato implementato il `CRUD completo`. 


### Validazione input (Frontend / Backend)

- `PublicEventForm.clean()`: data inizio/fine non nel passato; data fine ≥ data inizio
- `EventoPrivatoForm.clean()`: stesse regole + `invitation_deadline` non nel passato e ≤ data inizio
- `JoinEventView.post()`: blocca se `stato_evento == 'PASSATO'` o `max_participants` raggiunto
- `InviteUserView.post()`: blocca se `stato_evento == 'PASSATO'`

### Sicurezza

- `LoginRequiredMixin` su tutte le view che richiedono autenticazione
- `UserPassesTestMixin` + `test_func()` per controllo ruolo nelle azioni sensibili
- CSRF token su tutti i form
- `transaction.atomic()` + `select_for_update()` in `PaymentView` e per evitare conflitti in caso di `max_participants` raggiunto da più attendee simultaneamente
- Sessione: 30 minuti con rinnovo ad ogni richiesta (`SESSION_COOKIE_AGE = 1800`, `SESSION_SAVE_EVERY_REQUEST = True`)
- Organizer disattivati: `is_active = False` blocca `ModelBackend.authenticate()`; `CustomLoginView` intercetta e mostra "Utente Disattivato" al posto dell'errore generico

---

## Installazione locale

```bash
# 1. Clona il repository
git clone <URL_REPOSITORY>
cd ppmProject

# 2. Crea e attiva ambiente virtuale
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Applica le migrazioni (opzionale se si usa il db.sqlite3 incluso)
python manage.py migrate

# 5. Avvia il server
python manage.py runserver
```

Applicazione disponibile su `http://127.0.0.1:8000/`

---

## Database demo

File incluso: `db.sqlite3`

Contiene dati pre-caricati sufficienti per esplorare immediatamente tutti i flussi principali:
- 4 account demo con ruoli diversi
- 3 eventi di esempio (2 pubblici, 1 privato)

Per ricreare il database da zero:
```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Account demo

> Credenziali create esclusivamente per la valutazione del progetto.

| Username | Password | Ruolo | Note |
|----------|----------|-------|------|
| `admin` | `demo_admin` | Superadmin | Accesso `/admin/`, gestione organizer |
| `test_organizer` | `demo_org_1` | Organizer (attivo) | Crea/modifica/elimina eventi |
| `test_organizer_2` | `demo_org_2` | Organizer (attivo) | Test co-gestione e disattivazione |
| `test_attendee` | `demo_att_1` | Attendee | Iscrizioni, inviti, pagamento simulato |

---

## Scenario di test browser

### Flusso 0 — Admin gestisce organizer

1. Login con `admin` 
2. **Lista Utenti** → filtro **Organizer**
3. **Disattiva** su `test_organizer_2` → confermare
4. Verificare badge **Disattivo** nella riga
5. Logout → login con `test_organizer_2` → verificare messaggio **"Utente Disattivato"**
6. Rientrare come `admin` → **Attiva** → verificare login ripristinato

### Flusso 1 — Organizer crea e gestisce un evento pubblico

1. Login con `test_organizer` (scegliere se stessi come supervisor e organizer) 
2. **Lista Eventi** → **Nuovo Evento** → scegliere **Evento Pubblico**
3. Compilare: titolo, descrizione, date future, location; impostare `ticket_price = 10.00`, `max_participants = 1`, `public_visibility = True`; salvare
4. Aprire il dettaglio → verificare badge **PROGRAMMATO**
5. Login con `test_attendee` , aprire il dettaglio dell'evento → **Iscriviti**. 
6. **Modifica Evento** → cambiare titolo → salvare → verificare aggiornamento
7. **Elimina Evento** → confermare → verificare redirect alla lista


### Flusso 2 — Attendee si iscrive e paga

1. Login con `test_attendee`
2. Dalla lista eventi aprire l'evento pubblico con `public_visibility = True`
3. **Iscriviti** → se `ticket_price > 0`, redirect alla pagina pagamento simulato
4. Inserire dati carta fittizi → **Conferma Pagamento** → verificare `payment_status = PAID`
5. **Abbandona Evento** → verificare ritorno alla lista

### Flusso 3 — Admin disattiva un Organizer

1. Login con `admin`
2. **Lista Utenti** → filtro **Organizer**
3. **Disattiva** su `test_organizer_2` → confermare
4. Verificare badge **Disattivo** nella riga
5. Logout → login con `test_organizer_2` → verificare messaggio **"Utente Disattivato"**
6. Rientrare come `admin` → **Attiva** → verificare login ripristinato

### Flusso 4 — Azione negata (test permessi)

1. Login con `test_attendee`
2. Tentare di accedere direttamente a `/eventi/crea/` → verificare redirect al login o errore 403
3. Tentare di accedere al dettaglio di un evento privato senza invito → verificare errore/redirect
4. Dalla lista utenti verificare che non siano visibili gli account Organizer

---

## Possibili miglioramenti futuri

- Aggiungere reale sistema di pagamento con gestione più attenta delle transazioni
- Dunque modificare l'utente dando la possibiltà di salvare le carte  (per ora non possibile) in modo sicuro
- Aggiungere l'invio di mail as Service: dunque ad esempio per confermare un'iscrizione, un pagamento o un annullamento ecc...
- Aggiungere gestione di Immagini e video per gli eventi
- Aggiungere sistema di commenti ai post
- Aggiungere immagini profilo agli utenti
- Aggiungere test unitari
- Aggiungere testi di integrazione
- Aggiungere possibilità di vedere la pagina degli eventi anche senza essersi loggati
