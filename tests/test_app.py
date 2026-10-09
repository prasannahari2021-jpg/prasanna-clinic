import unittest

import app as clinic_app


class AppointmentSystemTests(unittest.TestCase):
    def setUp(self):
        clinic_app.app.config['TESTING'] = True
        self.client = clinic_app.app.test_client()

    def test_admin_login_page_is_available(self):
        response = self.client.get('/admin/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'admin', response.data.lower())

    def test_booking_api_creates_appointment_with_token(self):
        response = self.client.post('/api/book', data={
            'owner_name': 'John Doe',
            'mobile': '9876543210',
            'email': 'john@example.com',
            'pet_name': 'Bruno',
            'pet_type': 'Dog',
            'breed': 'Labrador',
            'age': '3',
            'gender': 'Male',
            'weight': '18',
            'service': 'Wellness Check',
            'appointment_date': '2026-08-10',
            'appointment_time': '10:00',
            'symptoms': 'Mild fever'
        })
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['token_number'].startswith('TKN'))

    def test_public_homepage_exposes_admin_login_link(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/admin/login', response.data)

    def test_my_appointments_page_is_available(self):
        response = self.client.get('/my-appointments')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'my appointments', response.data.lower())

    def test_my_appointments_page_shows_booking_history_for_token(self):
        created = clinic_app.create_appointment({
            'owner_name': 'Alice',
            'mobile': '9999999999',
            'email': 'alice@example.com',
            'pet_name': 'Milo',
            'pet_type': 'Dog',
            'breed': 'Pug',
            'age': '2',
            'gender': 'Male',
            'weight': '8',
            'service': 'Wellness Check',
            'appointment_date': '2026-09-01',
            'appointment_time': '11:00',
            'symptoms': 'Needs checkup'
        })

        response = self.client.get(f"/my-appointments?token={created['token_number']}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(created['token_number'].encode(), response.data)
        self.assertIn(b'2026-09-01', response.data)

    def test_success_page_shows_booking_details(self):
        response = self.client.get('/appointment/success?token=TKN000001')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'appointment successfully booked', response.data.lower())

    def test_admin_dashboard_lists_appointments(self):
        with self.client.session_transaction() as session:
            session['admin_logged_in'] = True
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
