import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from reservations.models import Room, Reservation, Clients
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='AdminPass123!'
    )


@pytest.fixture
def regular_user():
    return User.objects.create_user(
        username='regularuser',
        email='regular@example.com',
        password='RegularPass123!'
    )


@pytest.fixture
def auth_admin_client(api_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = admin_user
    return api_client


@pytest.fixture
def auth_regular_client(api_client, regular_user):
    refresh = RefreshToken.for_user(regular_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = regular_user
    return api_client


@pytest.fixture
def sample_rooms():
    rooms = []

    # Create various room types
    rooms.append(Room.objects.create(
        number=101,
        type='single',
        price_for_night=Decimal('100.00'),
        status='available',
        capacity=1,
        description='Cozy single room',
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': False,
            'jacuzzi': False,
            'tv': True,
            'breakfast_included': True
        }
    ))

    rooms.append(Room.objects.create(
        number=201,
        type='double',
        price_for_night=Decimal('150.00'),
        status='available',
        capacity=2,
        description='Comfortable double room',
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': True,
            'jacuzzi': False,
            'tv': True,
            'breakfast_included': True
        }
    ))

    rooms.append(Room.objects.create(
        number=301,
        type='suit',
        price_for_night=Decimal('300.00'),
        status='available',
        capacity=4,
        description='Luxury suite',
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': True,
            'jacuzzi': True,
            'tv': True,
            'breakfast_included': True
        }
    ))

    return rooms


class TestRoomManagement:
    """Test room management functionality"""

    def test_admin_room_crud_operations(self, auth_admin_client):
        """Test complete CRUD operations for rooms by admin"""

        # Create room
        room_data = {
            'number': 501,
            'type': 'deluxe',
            'price_for_night': '400.00',
            'status': 'available',
            'capacity': 3,
            'description': 'Deluxe room with ocean view',
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': True,
                'jacuzzi': True,
                'tv': True,
                'breakfast_included': True
            }
        }

        room_url = reverse('reservations:room-list')
        create_response = auth_admin_client.post(
            room_url, room_data, format='json')
        assert create_response.status_code == status.HTTP_201_CREATED

        room_id = create_response.data['id']

        # Read room
        detail_url = reverse('reservations:room-detail',
                             kwargs={'pk': room_id})
        read_response = auth_admin_client.get(detail_url)
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.data['number'] == 501

        # Update room
        update_data = room_data.copy()
        update_data['price_for_night'] = '450.00'
        update_data['status'] = 'cleaning'

        update_response = auth_admin_client.put(
            detail_url, update_data, format='json')
        assert update_response.status_code == status.HTTP_200_OK
        assert float(update_response.data['price_for_night']) == 450.00
        assert update_response.data['status'] == 'cleaning'

        # Delete room
        delete_response = auth_admin_client.delete(detail_url)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        verify_response = auth_admin_client.get(detail_url)
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND

    def test_regular_user_room_access(self, auth_regular_client, sample_rooms):
        """Test regular user access to rooms (read-only)"""

        # Can list rooms
        room_url = reverse('reservations:room-list')
        list_response = auth_regular_client.get(room_url)
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.data) == len(sample_rooms)

        # Can read specific room
        room_id = sample_rooms[0].id
        detail_url = reverse('reservations:room-detail',
                             kwargs={'pk': room_id})
        detail_response = auth_regular_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK

        # Cannot create room
        room_data = {
            'number': 999,
            'type': 'single',
            'price_for_night': '100.00',
            'status': 'available',
            'capacity': 1,
            'amenities': {
                'wifi': True,
                'air_conditioning': True,
                'minibar': False,
                'jacuzzi': False,
                'tv': True,
                'breakfast_included': True
            }
        }

        create_response = auth_regular_client.post(
            room_url, room_data, format='json')
        assert create_response.status_code == status.HTTP_403_FORBIDDEN


class TestReservationManagement:
    """Test reservation management functionality"""

    def test_overlapping_reservations_prevention(self, auth_admin_client, sample_rooms):
        """Test that overlapping reservations are prevented"""

        # Create two clients
        user1 = User.objects.create_user(
            username='user1', email='user1@example.com')
        user2 = User.objects.create_user(
            username='user2', email='user2@example.com')

        client1 = Clients.objects.create(
            user=user1,
            name='Client',
            lastname='One',
            document_number='11111111',
            email='client1@example.com'
        )

        client2 = Clients.objects.create(
            user=user2,
            name='Client',
            lastname='Two',
            document_number='22222222',
            email='client2@example.com'
        )

        room = sample_rooms[0]

        # Create first reservation
        reservation1_data = {
            'date_in': '2024-12-15',
            'date_out': '2024-12-17',
            'number_of_guests': 1,
            'client': client1.id,
            'room': room.id
        }

        reservation_url = reverse('reservations:reservation-list')
        response1 = auth_admin_client.post(
            reservation_url, reservation1_data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create overlapping reservation
        reservation2_data = {
            'date_in': '2024-12-16',
            'date_out': '2024-12-18',
            'number_of_guests': 1,
            'client': client2.id,
            'room': room.id
        }

        response2 = auth_admin_client.post(
            reservation_url, reservation2_data, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'not available for the selected dates' in str(response2.data)


class TestPermissionsAndSecurity:
    """Test permissions and security features"""

    def test_unauthenticated_access(self, api_client, sample_rooms):
        """Test that unauthenticated users cannot access protected endpoints"""

        # Cannot list rooms
        room_url = reverse('reservations:room-list')
        response = api_client.get(room_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Cannot check availability
        availability_url = reverse('reservations:room-availability')
        response = api_client.get(availability_url, {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Cannot access reservations
        reservation_url = reverse('reservations:reservation-list')
        response = api_client.get(reservation_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_room_amenities(self, auth_admin_client):
        """Test handling of invalid room amenities"""

        room_data = {
            'number': 999,
            'type': 'single',
            'price_for_night': '100.00',
            'status': 'available',
            'capacity': 1,
            'amenities': {
                'wifi': True,
                'air_conditioning': True
                # Missing required amenities
            }
        }

        room_url = reverse('reservations:room-list')
        response = auth_admin_client.post(room_url, room_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'amenities' in response.data

    def test_invalid_availability_params(self, auth_regular_client):
        """Test handling of invalid availability parameters"""

        availability_url = reverse('reservations:room-availability')

        # Missing required parameters
        response = auth_regular_client.get(availability_url, {
            'date_in': '2024-12-25'
            # Missing date_out
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Invalid date format
        response = auth_regular_client.get(availability_url, {
            'date_in': 'invalid-date',
            'date_out': '2024-12-27'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Past date
        past_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = auth_regular_client.get(availability_url, {
            'date_in': past_date,
            'date_out': '2024-12-27'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_client_profile(self, auth_regular_client):
        """Test prevention of duplicate client profiles"""

        client_data = {
            'name': 'John',
            'lastname': 'Doe',
            'document_number': '12345678',
            'street': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'country': 'USA',
            'email': 'john@example.com'
        }

        client_url = reverse('reservations:client-list')

        # Create first client profile
        response1 = auth_regular_client.post(
            client_url, client_data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create second client profile for same user
        client_data['email'] = 'different@example.com'
        response2 = auth_regular_client.post(
            client_url, client_data, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
