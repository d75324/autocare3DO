from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Service, Vehicle


class VehicleAccessTests(TestCase):
    """Cada usuario solo accede a sus vehículos (y el mecánico, a los asignados)."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('dueno@example.com', password='pass12345')
        cls.other = User.objects.create_user('otro@example.com', password='pass12345')
        cls.mechanic = User.objects.create_user('mecanico@example.com', password='pass12345')

        cls.car = Vehicle.objects.create(
            owner=cls.owner, plate='abc123', brand='Fiat', moddel='Uno',
            color='Rojo', mileage=1000, car_mechanic=cls.mechanic,
        )
        Service.objects.create(vehicle=cls.car, kilometers=1500,
                               service_type='Cambio aceite', cost=100)

    def urls(self):
        return {
            'detail': reverse('vehicle_detail', args=[self.car.pk]),
            'csv': reverse('download_csv', args=[self.car.pk]),
            'delete': reverse('vehicle_delete', args=[self.car.pk]),
            'add_service': reverse('add_service', args=[self.car.pk]),
        }

    # --- sin login ---------------------------------------------------------
    def test_anonymous_is_redirected_to_login(self):
        protected = list(self.urls().values()) + [
            reverse('vehicle_list'), reverse('profile'), reverse('servicelist'),
        ]
        for url in protected:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertTrue(response['Location'].startswith(reverse('login')), url)

    def test_anonymous_cannot_delete(self):
        self.client.post(self.urls()['delete'])
        self.assertTrue(Vehicle.objects.filter(pk=self.car.pk).exists())

    # --- otro usuario ------------------------------------------------------
    def test_other_user_gets_404_everywhere(self):
        self.client.force_login(self.other)
        for name, url in self.urls().items():
            self.assertEqual(self.client.get(url).status_code, 404, name)

    def test_other_user_cannot_delete(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.urls()['delete']).status_code, 404)
        self.assertTrue(Vehicle.objects.filter(pk=self.car.pk).exists())
        self.assertEqual(Service.objects.filter(vehicle=self.car).count(), 1)

    # --- dueño -------------------------------------------------------------
    def test_owner_has_full_access(self):
        self.client.force_login(self.owner)
        urls = self.urls()
        self.assertEqual(self.client.get(urls['detail']).status_code, 200)
        csv_response = self.client.get(urls['csv'])
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn(b'ABC123', csv_response.content)
        self.assertEqual(self.client.post(urls['delete']).status_code, 302)
        self.assertFalse(Vehicle.objects.filter(pk=self.car.pk).exists())
        self.assertFalse(Service.objects.exists())

    # --- mecánico asignado -------------------------------------------------
    def test_assigned_mechanic_can_view_and_download_but_not_delete(self):
        self.client.force_login(self.mechanic)
        urls = self.urls()
        self.assertEqual(self.client.get(urls['detail']).status_code, 200)
        self.assertEqual(self.client.get(urls['csv']).status_code, 200)
        self.assertEqual(self.client.get(urls['add_service']).status_code, 200)
        self.assertEqual(self.client.post(urls['delete']).status_code, 404)
        self.assertTrue(Vehicle.objects.filter(pk=self.car.pk).exists())

    def test_assigned_mechanic_can_add_service(self):
        self.client.force_login(self.mechanic)
        response = self.client.post(self.urls()['add_service'], {
            'vehicle': self.car.pk, 'date': '2026-10-25', 'kilometers': 2000,
            'service_type': 'Cambio aceite', 'coments': '', 'cost': 50,
        })
        self.assertEqual(response.status_code, 302)
        self.car.refresh_from_db()
        self.assertEqual(self.car.mileage, 2000)

    def test_cannot_add_service_to_foreign_vehicle_via_form(self):
        """Aunque la URL sea de un auto propio, el campo 'vehicle' no acepta autos ajenos."""
        own = Vehicle.objects.create(owner=self.other, plate='zzz999', brand='Fiat',
                                     moddel='Palio', color='Azul', mileage=10)
        self.client.force_login(self.other)
        self.client.post(reverse('add_service', args=[own.pk]), {
            'vehicle': self.car.pk, 'date': '2026-10-25', 'kilometers': 9999,
            'service_type': 'Cambio aceite', 'coments': '', 'cost': 1,
        })
        self.assertEqual(Service.objects.filter(vehicle=self.car).count(), 1)
