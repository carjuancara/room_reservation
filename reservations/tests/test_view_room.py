import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from reservations.models import Room
from django.contrib.auth.models import User

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
def test_room():
    return Room.objects.create(
        number=1,
        type='single',
        price_for_night=100.00,
        status='available',
        capacity=2,
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': False,
            'jacuzzi': False,
            'tv': True,
            'breakfast_included': True
        }
    )


class TestRoomViewSet:
    def test_list_rooms_as_admin(self, api_client, admin_user, test_room):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:room-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_rooms_as_regular_user(self, api_client, regular_user, test_room):
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:room-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_room_as_admin(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:room-list')
        data = {
            'number': 2,
            'type': 'double',
            'price_for_night': 150.00,
            'status': 'available',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Room.objects.count() == 1

    def test_create_room_as_regular_user(self, api_client, regular_user):
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:room-list')
        data = {
            'number': 2,
            'type': 'double',
            'price_for_night': 150.00,
            'status': 'available',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_room_as_admin(self, api_client, admin_user, test_room):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:room-detail', kwargs={'pk': test_room.pk})
        data = {
            'number': test_room.number,
            'type': 'double',
            'price_for_night': 150.00,
            'status': 'available',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }
        response = api_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        test_room.refresh_from_db()
        assert test_room.type == 'double'

    def test_delete_room_as_admin(self, api_client, admin_user, test_room):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:room-detail', kwargs={'pk': test_room.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Room.objects.count() == 0

    def test_delete_room_as_regular_user(self, api_client, regular_user, test_room):
        api_client.force_authenticate(user=regular_user)
        url = reverse('reservations:room-detail', kwargs={'pk': test_room.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_room_with_invalid_data(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:room-list')
        data = {
            'number': 'abc',
            'type': 'double',
            'price_for_night': 150.00,
            'status': 'available',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_room_with_invalid_data(self, api_client, admin_user, test_room):
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:room-detail', kwargs={'pk': test_room.pk})
        data = {
            'number': test_room.number,
            'type': 'invalid_type',
            'price_for_night': 150.00,
            'status': 'available',
            'capacity': 2,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }
        response = api_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
