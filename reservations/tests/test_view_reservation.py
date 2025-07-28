import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from reservations.models import Clients, Room, Reservation
from django.contrib.auth.models import User
from datetime import datetime, timedelta

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )


@pytest.fixture
def regular_user():
    return User.objects.create_user(
        username='user',
        email='user@example.com',
        password='user123'
    )


@pytest.fixture
def test_client():
    return Clients.objects.create(
        name='John',
        lastname='Doe',
        document_number='123456789',
        street='Main St',
        city='City',
        state='State',
        country='Country',
        email='john@example.com'
    )


@pytest.fixture
def test_room():
    return Room.objects.create(
        number=1,
        type='single',
        price_for_night=100.00,
        status='available',
        capacity=2,
        amenities={'wifi': True, 'air_conditioning': True}
    )


@pytest.fixture
def test_reservation(test_client, test_room):
    return Reservation.objects.create(
        date_in=datetime.now().date(),
        date_out=datetime.now().date() + timedelta(days=2),
        status='confirmed',
        total_price=200.00,
        client=test_client,
        room=test_room
    )


class TestReservationViewSet:
    def test_list_reservations_as_admin(self, api_client, admin_user, test_reservation):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_reservations_as_regular_user(self, api_client, regular_user, test_reservation):
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:reservation-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Regular users only see their own reservations
        assert len(response.data) == 0

    def test_create_reservation_as_admin(self, api_client, admin_user, test_client, test_room):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')
        data = {
            'date_in': datetime.now().date().isoformat(),
            'date_out': (datetime.now() + timedelta(days=2)).date().isoformat(),
            'status': 'confirmed',
            'client': test_client.id,
            'room': test_room.id
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Reservation.objects.count() == 1

    def test_create_reservation_as_regular_user(self, api_client, regular_user, test_client, test_room):
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:reservation-list')
        data = {
            'date_in': datetime.now().date().isoformat(),
            'date_out': (datetime.now() + timedelta(days=2)).date().isoformat(),
            'status': 'confirmed',
            'client': test_client.id,
            'room': test_room.id
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_my_reservations(self, api_client, regular_user, test_client, test_reservation):
        test_client.user = regular_user
        test_client.save()
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:reservation-my_reservations')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_update_reservation_as_admin(self, api_client, admin_user, test_reservation):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-detail',
                      kwargs={'pk': test_reservation.pk})
        data = {
            'date_in': test_reservation.date_in.isoformat(),
            'date_out': test_reservation.date_out.isoformat(),
            'status': 'cancelled',
            'client': test_reservation.client.id,
            'room': test_reservation.room.id
        }
        response = api_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        test_reservation.refresh_from_db()
        assert test_reservation.status == 'cancelled'

    def test_update_reservation_as_regular_user(self, api_client, regular_user, test_reservation):
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:reservation-detail',
                      kwargs={'pk': test_reservation.pk})
        data = {
            'date_in': test_reservation.date_in.isoformat(),
            'date_out': test_reservation.date_out.isoformat(),
            'status': 'cancelled',
            'client': test_reservation.client.id,
            'room': test_reservation.room.id
        }
        response = api_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_reservation_as_admin(self, api_client, admin_user, test_reservation):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-detail',
                      kwargs={'pk': test_reservation.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Reservation.objects.count() == 0

    def test_delete_reservation_as_regular_user(self, api_client, regular_user, test_reservation):
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:reservation-detail',
                      kwargs={'pk': test_reservation.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_reservation_with_invalid_dates(self, api_client, admin_user, test_client, test_room):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')
        data = {
            'date_in': datetime.now().date().isoformat(),
            'date_out': datetime.now().date().isoformat(),  # Same day
            'status': 'confirmed',
            'client': test_client.id,
            'room': test_room.id
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_reservation_with_overlapping_dates(self, api_client, admin_user, test_client, test_room):
        # Create first reservation
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')
        data = {
            'date_in': datetime.now().date().isoformat(),
            'date_out': (datetime.now() + timedelta(days=2)).date().isoformat(),
            'status': 'confirmed',
            'client': test_client.id,
            'room': test_room.id
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        # Try to create overlapping reservation
        data['date_in'] = (datetime.now() + timedelta(days=1)
                           ).date().isoformat()
        data['date_out'] = (
            datetime.now() + timedelta(days=3)).date().isoformat()
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
