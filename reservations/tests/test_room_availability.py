import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from reservations.models import Room, Reservation, Clients
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='TestPass123!'
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='AdminPass123!'
    )


@pytest.fixture
def test_client(test_user):
    return Clients.objects.create(
        user=test_user,
        name='John',
        lastname='Doe',
        document_number='12345678',
        street='123 Main St',
        city='New York',
        state='NY',
        country='USA',
        email='john@example.com'
    )


@pytest.fixture
def test_rooms():
    rooms = []

    # Single room
    rooms.append(Room.objects.create(
        number=101,
        type='single',
        price_for_night=Decimal('100.00'),
        status='available',
        capacity=1,
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': False,
            'jacuzzi': False,
            'tv': True,
            'breakfast_included': True
        }
    ))

    # Double room
    rooms.append(Room.objects.create(
        number=102,
        type='double',
        price_for_night=Decimal('150.00'),
        status='available',
        capacity=2,
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': True,
            'jacuzzi': False,
            'tv': True,
            'breakfast_included': True
        }
    ))

    # Suite room
    rooms.append(Room.objects.create(
        number=201,
        type='suit',
        price_for_night=Decimal('300.00'),
        status='available',
        capacity=4,
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': True,
            'jacuzzi': True,
            'tv': True,
            'breakfast_included': True
        }
    ))

    # Maintenance room (should not appear in availability)
    rooms.append(Room.objects.create(
        number=103,
        type='single',
        price_for_night=Decimal('100.00'),
        status='maintenance',
        capacity=1,
        amenities={
            'wifi': True,
            'air_conditioning': True,
            'minibar': False,
            'jacuzzi': False,
            'tv': True,
            'breakfast_included': True
        }
    ))

    return rooms


class TestRoomAvailability:
    def test_availability_endpoint_requires_authentication(self, api_client, test_rooms):
        """Test that availability endpoint requires authentication"""
        url = reverse('reservations:room-availability')
        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_availability_basic_query(self, api_client, test_user, test_rooms):
        """Test basic availability query"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27',
            'guests': 1
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'available_rooms' in data
        assert 'total_available' in data
        assert 'date_in' in data
        assert 'date_out' in data
        assert 'guests' in data

        # Should have 3 available rooms (excluding maintenance room)
        assert data['total_available'] == 3
        assert len(data['available_rooms']) == 3

    def test_availability_missing_required_params(self, api_client, test_user, test_rooms):
        """Test availability query with missing required parameters"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        # Missing date_out
        response = api_client.get(url, {
            'date_in': '2025-12-25'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.json()

        # Missing date_in
        response = api_client.get(url, {
            'date_out': '2025-12-27'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.json()

    def test_availability_invalid_date_format(self, api_client, test_user, test_rooms):
        """Test availability query with invalid date format"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        response = api_client.get(url, {
            'date_in': 'invalid-date',
            'date_out': '2025-12-27'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.json()

    def test_availability_invalid_date_range(self, api_client, test_user, test_rooms):
        """Test availability query with invalid date range"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        # date_out before date_in
        response = api_client.get(url, {
            'date_in': '2025-12-27',
            'date_out': '2025-12-25'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.json()

    def test_availability_past_date(self, api_client, test_user, test_rooms):
        """Test availability query with past date"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        past_date = date.today() - timedelta(days=1)
        response = api_client.get(url, {
            'date_in': past_date.strftime('%Y-%m-%d'),
            'date_out': '2025-12-27'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.json()

    def test_availability_filter_by_capacity(self, api_client, test_user, test_rooms):
        """Test availability filtering by guest capacity"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        # Request for 4 guests - only suite should be available
        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27',
            'guests': 4
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_available'] == 1
        assert data['available_rooms'][0]['capacity'] >= 4

    def test_availability_filter_by_room_type(self, api_client, test_user, test_rooms):
        """Test availability filtering by room type"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27',
            'room_type': 'single'
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_available'] == 1
        assert data['available_rooms'][0]['room_type'] == 'single'

    def test_availability_excludes_reserved_rooms(self, api_client, test_user, test_client, test_rooms):
        """Test that availability excludes rooms with existing reservations"""
        api_client.force_authenticate(user=test_user)

        # Create a reservation for one room
        room = test_rooms[0]  # single room
        Reservation.objects.create(
            date_in=date(2025, 12, 25),
            date_out=date(2025, 12, 27),
            number_of_guests=1,
            status='confirmed',
            client=test_client,
            room=room
        )

        url = reverse('reservations:room-availability')
        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27'
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have 2 available rooms (excluding reserved and maintenance rooms)
        assert data['total_available'] == 2

        # Reserved room should not be in the list
        room_numbers = [room['room_number'] for room in data['available_rooms']]
        assert room.number not in room_numbers

    def test_availability_excludes_maintenance_rooms(self, api_client, test_user, test_rooms):
        """Test that availability excludes rooms in maintenance"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27'
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check that maintenance room is not in results
        room_numbers = [room['room_number'] for room in data['available_rooms']]
        maintenance_room_number = 103  # From fixture
        assert maintenance_room_number not in room_numbers

    def test_availability_price_calculation(self, api_client, test_user, test_rooms):
        """Test that availability includes correct price calculations"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27'  # 2 nights
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for room in data['available_rooms']:
            expected_total = room['price_per_night'] * room['nights']
            assert float(room['total_price']) == float(expected_total)
            assert room['nights'] == 2

    def test_availability_overlapping_reservation_conflict(self, api_client, test_user, test_client, test_rooms):
        """Test that overlapping reservations are properly excluded"""
        api_client.force_authenticate(user=test_user)

        room = test_rooms[0]

        # Create reservation from Dec 24-26
        Reservation.objects.create(
            date_in=date(2025, 12, 24),
            date_out=date(2025, 12, 26),
            number_of_guests=1,
            status='confirmed',
            client=test_client,
            room=room
        )

        url = reverse('reservations:room-availability')

        # Query for Dec 25-27 (overlaps with existing reservation)
        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27'
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        room_numbers = [room['room_number'] for room in data['available_rooms']]
        assert room.number not in room_numbers

    def test_availability_cancelled_reservations_dont_block(self, api_client, test_user, test_client, test_rooms):
        """Test that cancelled reservations don't block availability"""
        api_client.force_authenticate(user=test_user)

        room = test_rooms[0]

        # Create cancelled reservation
        Reservation.objects.create(
            date_in=date(2025, 12, 25),
            date_out=date(2025, 12, 27),
            number_of_guests=1,
            status='cancelled',
            client=test_client,
            room=room
        )

        url = reverse('reservations:room-availability')
        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27'
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Room should be available since reservation is cancelled
        room_numbers = [room['room_number'] for room in data['available_rooms']]
        assert room.number in room_numbers

    def test_availability_response_structure(self, api_client, test_user, test_rooms):
        """Test that availability response has correct structure"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27',
            'guests': 2
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check main structure
        required_fields = ['date_in', 'date_out', 'guests', 'available_rooms', 'total_available']
        for field in required_fields:
            assert field in data

        # Check room structure
        if data['available_rooms']:
            room = data['available_rooms'][0]
            required_room_fields = [
                'room_id', 'room_number', 'room_type', 'capacity',
                'price_per_night', 'total_price', 'nights', 'description', 'amenities'
            ]
            for field in required_room_fields:
                assert field in room

    def test_availability_default_guests_value(self, api_client, test_user, test_rooms):
        """Test that guests parameter defaults to 1 when not provided"""
        api_client.force_authenticate(user=test_user)
        url = reverse('reservations:room-availability')

        response = api_client.get(url, {
            'date_in': '2025-12-25',
            'date_out': '2025-12-27'
            # guests parameter not provided
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['guests'] == 1
