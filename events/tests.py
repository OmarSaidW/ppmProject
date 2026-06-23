from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from events.models import Event, Registration
import datetime

User = get_user_model()

class EventAppTests(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(username='test_user', password='password123', ruolo='ATTENDEE')
        self.organizer = User.objects.create_user(username='org_user', password='password123', ruolo='ORGANIZER')
        
        # Log in the user
        self.client = Client()
        self.client.login(username='test_user', password='password123')
        
    def test_user_profile_ajax_events_pagination(self):
        """Task 1: User profile AJAX events list returns at most 30 events, sorted by date descending."""
        # Create 35 events and register the user for all of them
        now = timezone.now()
        registrations = []
        for i in range(35):
            event = Event.objects.create(
                title=f"Event {i}",
                description=f"Desc {i}",
                date=now - datetime.timedelta(days=i),
                location=f"Location {i}",
                supervisor=self.organizer
            )
            # Create registration
            registrations.append(
                Registration(user=self.user, event=event, stato='ATTIVO')
            )
        Registration.objects.bulk_create(registrations)

        # Query first page via AJAX
        response = self.client.get(
            reverse('dettaglio_profilo', kwargs={'pk': self.user.pk}),
            {'ajax': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify 30 events are returned
        self.assertEqual(len(data['events']), 30)
        self.assertTrue(data['has_next'])
        self.assertFalse(data['has_previous'])
        self.assertEqual(data['num_pages'], 2)
        
        # Verify sorting (descending by date)
        # Event 0 is the most recent (now), Event 29 is now - 29 days
        self.assertEqual(data['events'][0]['title'], "Event 0")
        self.assertEqual(data['events'][29]['title'], "Event 29")

        # Query second page
        response = self.client.get(
            reverse('dettaglio_profilo', kwargs={'pk': self.user.pk}),
            {'ajax': '1', 'page': '2'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['events']), 5)
        self.assertFalse(data['has_next'])
        self.assertTrue(data['has_previous'])
        self.assertEqual(data['events'][0]['title'], "Event 30")

    def test_event_list_limit_to_50(self):
        """Task 2b: Event list page limits the loaded events to 50."""
        # Create 60 events
        now = timezone.now()
        for i in range(60):
            event = Event.objects.create(
                title=f"Event {i}",
                description=f"Desc {i}",
                date=now + datetime.timedelta(hours=i),
                location=f"Location {i}",
                supervisor=self.organizer
            )
            # Register user to the event so it shows up in their list
            Registration.objects.create(user=self.user, event=event, stato='ATTIVO')
            
        response = self.client.get(reverse('lista_eventi'))
        self.assertEqual(response.status_code, 200)
        
        # Check context events count is limited to 50
        events_in_context = response.context['eventi']
        self.assertEqual(len(events_in_context), 50)

    def test_calendar_events_range_limit(self):
        """Task 2b: Calendar events JSON endpoint limits to 6 months before and after."""
        now = timezone.now()
        
        # Event within range (e.g. 1 month ago)
        event_in = Event.objects.create(
            title="In Range Event",
            description="Desc",
            date=now - datetime.timedelta(days=30),
            location="Location",
            supervisor=self.organizer
        )
        Registration.objects.create(user=self.user, event=event_in, stato='ATTIVO')
        
        # Event out of range (e.g. 7 months ago)
        event_out = Event.objects.create(
            title="Out of Range Event",
            description="Desc",
            date=now - datetime.timedelta(days=210),
            location="Location",
            supervisor=self.organizer
        )
        Registration.objects.create(user=self.user, event=event_out, stato='ATTIVO')
        
        response = self.client.get(reverse('eventi_json'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only contain the in-range event
        event_titles = [e['title'] for e in data]
        self.assertIn("In Range Event", event_titles)
        self.assertNotIn("Out of Range Event", event_titles)

    def test_user_profile_ajax_events_roles(self):
        """Task 1: User profile AJAX events lists events where user is organizer/supervisor/attendee."""
        now = timezone.now()
        
        # 1. Event as attendee
        event_att = Event.objects.create(
            title="Attendee Event",
            description="Desc",
            date=now,
            location="Location",
            supervisor=self.organizer
        )
        Registration.objects.create(user=self.user, event=event_att, stato='ATTIVO')
        
        # 2. Event as organizer
        event_org = Event.objects.create(
            title="Organizer Event",
            description="Desc",
            date=now - datetime.timedelta(days=1),
            location="Location",
            supervisor=self.organizer
        )
        event_org.organizers.add(self.user)
        
        # 3. Event as supervisor
        event_sup = Event.objects.create(
            title="Supervisor Event",
            description="Desc",
            date=now - datetime.timedelta(days=2),
            location="Location",
            supervisor=self.user
        )
        
        # Query via AJAX
        response = self.client.get(
            reverse('dettaglio_profilo', kwargs={'pk': self.user.pk}),
            {'ajax': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data['events']), 3)
        titles = [e['title'] for e in data['events']]
        self.assertIn("Attendee Event", titles)
        self.assertIn("Organizer Event", titles)
        self.assertIn("Supervisor Event", titles)

    def test_event_update_permissions(self):
        """Test permissions for EventUpdateView."""
        now = timezone.now()
        event = Event.objects.create(
            title="Edit Test Event",
            description="Original Description",
            date=now,
            location="Original Location",
            supervisor=self.organizer
        )
        
        # 1. Attendee tries to access edit page -> 403 Forbidden
        response = self.client.get(reverse('modifica_evento', kwargs={'pk': event.pk}))
        self.assertEqual(response.status_code, 403)
        
        response = self.client.post(reverse('modifica_evento', kwargs={'pk': event.pk}), {
            'title': 'New Title',
            'description': 'New Description',
            'date': (now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'location': 'New Location',
        })
        self.assertEqual(response.status_code, 403)
        
        # 2. Login as event organizer and try to edit -> 200 OK and successful redirect
        org_user_2 = User.objects.create_user(username='org_user_2', password='password123', ruolo='ORGANIZER')
        event.organizers.add(org_user_2)
        
        client_org = Client()
        client_org.login(username='org_user_2', password='password123')
        
        response = client_org.get(reverse('modifica_evento', kwargs={'pk': event.pk}))
        self.assertEqual(response.status_code, 200)
        
        new_date = now + datetime.timedelta(days=1)
        response = client_org.post(reverse('modifica_evento', kwargs={'pk': event.pk}), {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'date': new_date.strftime('%Y-%m-%dT%H:%M'),
            'location': 'Updated Location',
            'organizers': [org_user_2.id]
        })
        self.assertRedirects(response, reverse('dettaglio_evento', kwargs={'pk': event.pk}))
        
        event.refresh_from_db()
        self.assertEqual(event.title, 'Updated Title')
        self.assertEqual(event.description, 'Updated Description')
        self.assertEqual(event.location, 'Updated Location')

