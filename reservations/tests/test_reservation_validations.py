import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from reservations.models import Room, Reservation, Clients
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
def test_room():
    return Room.objects.create(
        number=101,
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
    )


@pytest.fixture
def maintenance_room():
    return Room.objects.create(
        number=102,
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
    )


class TestReservationValidations:
    def test_date_validation_date_out_before_date_in(self, test_client, test_room):
        """Test that date_out must be after date_in"""
        reservation = Reservation(
            date_in=date(2024, 12, 27),
            date_out=date(2024, 12, 25),  # Before date_in
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        with pytest.raises(ValidationError) as exc_info:
            reservation.full_clean()

        assert 'departure date must be after the arrival date' in str(
            exc_info.value)

    def test_date_validation_same_dates(self, test_client, test_room):
        """Test that date_out cannot be the same as date_in"""
        same_date = date(2024, 12, 25)
        reservation = Reservation(
            date_in=same_date,
            date_out=same_date,
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        with pytest.raises(ValidationError) as exc_info:
            reservation.full_clean()

        assert 'departure date must be after the arrival date' in str(
            exc_info.value)

    def test_guest_number_validation_zero_guests(self, test_client, test_room):
        """Test that number of guests must be at least 1"""
        reservation = Reservation(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=0,
            client=test_client,
            room=test_room
        )

        with pytest.raises(ValidationError) as exc_info:
            reservation.full_clean()

        assert 'number of guests must be at least 1' in str(exc_info.value)

    def test_guest_number_validation_negative_guests(self, test_client, test_room):
        """Test that number of guests cannot be negative"""
        reservation = Reservation(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=-1,
            client=test_client,
            room=test_room
        )

        with pytest.raises(ValidationError) as exc_info:
            reservation.full_clean()

        assert 'number of guests must be at least 1' in str(exc_info.value)

    def test_capacity_validation_exceeds_room_capacity(self, test_client, test_room):
        """Test that number of guests cannot exceed room capacity"""
        reservation = Reservation(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=5,  # Room capacity is 2
            client=test_client,
            room=test_room
        )

        with pytest.raises(ValidationError) as exc_info:
            reservation.full_clean()

        assert 'room does not have capacity for the number of guests' in str(
            exc_info.value)

    def test_room_status_validation_maintenance_room(self, test_client, maintenance_room):
        """Test that reservations cannot be made for rooms in maintenance"""
        reservation = Reservation(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            client=test_client,
            room=maintenance_room
        )

        with pytest.raises(ValidationError) as exc_info:
            reservation.full_clean()

        assert 'room is not available due to its current status' in str(
            exc_info.value)

    def test_overlapping_reservation_validation(self, test_client, test_room):
        """Test that overlapping reservations are not allowed"""
        # Create first reservation
        Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        # Try to create overlapping reservation
        overlapping_reservation = Reservation(
            date_in=date(2024, 12, 26),
            date_out=date(2024, 12, 28),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        with pytest.raises(ValidationError) as exc_info:
            overlapping_reservation.full_clean()

        assert 'room is not available for the selected dates' in str(
            exc_info.value)

    def test_overlapping_reservation_different_statuses(self, test_client, test_room):
        """Test overlapping validation considers only pending and confirmed reservations"""
        # Create cancelled reservation
        Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            status='cancelled',
            client=test_client,
            room=test_room
        )

        # Should be able to create reservation over cancelled one
        new_reservation = Reservation(
            date_in=date(2024, 12, 26),
            date_out=date(2024, 12, 28),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        # Should not raise ValidationError
        new_reservation.full_clean()

    def test_automatic_price_calculation(self, test_client, test_room):
        """Test that total price is calculated automatically"""
        reservation = Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),  # 2 nights
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        expected_price = Decimal('300.00')  # 2 nights * 150.00
        assert reservation.total_price == expected_price

    def test_manual_price_override(self, test_client, test_room):
        """Test that manually set price is not overridden"""
        manual_price = Decimal('200.00')
        reservation = Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            total_price=manual_price,
            client=test_client,
            room=test_room
        )

        assert reservation.total_price == manual_price

    def test_exact_same_dates_different_rooms(self, test_client, test_room):
        """Test that same dates are allowed for different rooms"""
        # Create second room
        room2 = Room.objects.create(
            number=201,
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
        )

        # Create first reservation
        Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        # Should be able to create reservation for same dates in different room
        reservation2 = Reservation(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            client=test_client,
            room=room2
        )

        # Should not raise ValidationError
        reservation2.full_clean()

    def test_adjacent_reservations_allowed(self, test_client, test_room):
        """Test that adjacent reservations (checkout/checkin same day) are allowed"""
        # Create first reservation
        Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        # Create adjacent reservation (starts when first one ends)
        adjacent_reservation = Reservation(
            date_in=date(2024, 12, 27),
            date_out=date(2024, 12, 29),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        # Should not raise ValidationError
        adjacent_reservation.full_clean()


class TestReservationSerializerValidations:
    def test_serializer_date_validation(self, api_client, admin_user, test_client, test_room):
        """Test serializer date validation through API"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')

        data = {
            'date_in': '2024-12-27',
            'date_out': '2024-12-25',  # Before date_in
            'number_of_guests': 1,
            'client': test_client.id,
            'room': test_room.id
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'departure date must be after the arrival date' in str(
            response.data)

    def test_serializer_capacity_validation(self, api_client, admin_user, test_client, test_room):
        """Test serializer capacity validation through API"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')

        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 5,  # Exceeds room capacity of 2
            'client': test_client.id,
            'room': test_room.id
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'room capacity is' in str(response.data)

    def test_serializer_availability_validation(self, api_client, admin_user, test_client, test_room):
        """Test serializer availability validation through API"""
        # Create existing reservation
        Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')

        data = {
            'date_in': '2024-12-26',
            'date_out': '2024-12-28',
            'number_of_guests': 1,
            'client': test_client.id,
            'room': test_room.id
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'room is not available for the selected dates' in str(
            response.data)

    def test_serializer_room_status_validation(self, api_client, admin_user, test_client, maintenance_room):
        """Test serializer room status validation through API"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')

        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 1,
            'client': test_client.id,
            'room': maintenance_room.id
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'room is not available due to its current status' in str(
            response.data)

    def test_serializer_guest_validation(self, api_client, admin_user, test_client, test_room):
        """Test serializer guest number validation through API"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')

        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 0,
            'client': test_client.id,
            'room': test_room.id
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'number of guests must be at least 1' in str(response.data)

    def test_successful_reservation_creation(self, api_client, admin_user, test_client, test_room):
        """Test successful reservation creation with valid data"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-list')

        data = {
            'date_in': '2024-12-25',
            'date_out': '2024-12-27',
            'number_of_guests': 2,
            'client': test_client.id,
            'room': test_room.id
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        # Verify reservation was created correctly
        reservation = Reservation.objects.get(id=response.data['id'])
        assert reservation.date_in == date(2024, 12, 25)
        assert reservation.date_out == date(2024, 12, 27)
        assert reservation.number_of_guests == 2
        assert reservation.total_price == Decimal(
            '300.00')  # 2 nights * 150.00

    def test_update_reservation_validation(self, api_client, admin_user, test_client, test_room):
        """Test validation when updating existing reservation"""
        # Create initial reservation
        reservation = Reservation.objects.create(
            date_in=date(2024, 12, 25),
            date_out=date(2024, 12, 27),
            number_of_guests=1,
            client=test_client,
            room=test_room
        )

        api_client.force_authenticate(user=admin_user)
        url = reverse('reservations:reservation-detail',
                      kwargs={'pk': reservation.pk})

        # Try to update with invalid dates
        data = {
            'date_in': '2024-12-27',
            'date_out': '2024-12-25',  # Invalid range
            'number_of_guests': 1,
            'client': test_client.id,
            'room': test_room.id
        }

        response = api_client.put(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
